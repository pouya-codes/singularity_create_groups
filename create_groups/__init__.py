import re
import os
import enum
import glob
import json
import random
import argparse
import itertools
import functools
import sys
import os.path

import h5py
import fnmatch
import numpy as np

import submodule_utils as utils
from submodule_utils.mixins import OutputMixin
from submodule_utils.metadata.group import (
        convert_yiping_to_mitch_format,
        convert_mitch_to_yiping_format)

default_component_id = 'create_groups'
default_seed = 256
default_n_groups = 3
default_subtypes = {'MMRD':0, 'P53ABN': 1, 'P53WT': 2, 'POLE': 3}
default_patch_pattern = 'annotation/subtype/slide'
default_filter_labels = {}
default_dataset_origin = ['ovcare']
default_min_patches = 10
default_max_patches = 1000000

class GroupCreator(OutputMixin):
    """Class that generates N groups that contain unique patients

    Attributes
    ----------
    seed : int
        seed for random shuffle

    n_groups : int
        The number of groups in groups file

    is_binary : bool
        Whether we want to categorize patches by the Tumor/Normal category (true) or by the subtype category (false)

    CategoryEnum : enum.Enum
        The enum representing the categories and is one of (SubtypeEnum, BinaryEnum)

    is_multiscale : bool
        Whether patches have multiple scales aka. different magnifications i.e.
        For non-multiscale patch, patch id has format: /subtype/slide_id/patch_location
        For multiscale patch, patch id has format: /subtype/slide_id/magnification/patch_location

    balance_patches : str or (tuple of str and int)
        Whether we want to balance the patches in each category. Options:
         - 'overall': we will select the number of patches of every (group, category) to the number of patches in (group, category) that is the smallest.

    dataset_origin : list of str
        The origins of the slide dataset the patches are generated from. One of DATASET_ORIGINS

    patch_location : str
        root directory of all patches of a study. The patch directory structure is '/patch_location/patch_pattern/x_y.png'

    hd5_location : str
        root directory of all hd5 of a study.

    patch_pattern : dict
        Dictionary describing the directory structure of the patch paths.
        A non-multiscale patch can be contained in a directory /path/to/patch/rootdir/Tumor/MMRD/VOA-1234/1_2.png so its patch_pattern is annotation/subtype/slide.
        A multiscale patch can be contained in a directory /path/to/patch/rootdir/Stroma/P53ABN/VOA-1234/10/3_400.png so its patch pattern is annotation/subtype/slide/magnification

    out_location : str
        full path of the groups file (i.e. /path/to/patient_groups.json)

    min_patches : int
        Only include from slides that have at least min_patches number of patches

    max_patches : int
        Only include from slides that have at most max_patches number of patches

    max_patient_patches : int
        Select at most max_patient_patches number of patches from each patient

    TODO: fix documentation of balance_patches
    """

    def get_patch_paths(self):
        """Get patch paths from patch location that match the patch paths. Filters patch paths by values of words.

        Returns
        -------
        list of str
            List of patch paths
        """
        patch_paths = []
        patch_path_wildcard = self.patch_location
        patterns = sorted([[v, k] for k, v in self.patch_pattern.items()],
                key=lambda x: x[0])
        patterns = map(lambda x: x[1], patterns)
        for word in patterns:
            if word in self.filter_labels:
                if word=='subtype':
                    patch_path_wildcard = os.path.join(patch_path_wildcard, '**')
                else:
                    patch_path_wildcard = os.path.join(patch_path_wildcard,
                                                       self.filter_labels[word])
            else:
                patch_path_wildcard = os.path.join(patch_path_wildcard, '**')
        patch_path_wildcard = os.path.join(patch_path_wildcard, r'*.[jp][pn]g')
        
        if 'subtype' in self.filter_labels:
            new_patch_path_wildcards = utils.get_subtype_paths(self.filter_labels['subtype'],
                                                               self.patch_pattern,
                                                               patch_path_wildcard)
            for new_patch_path_wildcard in new_patch_path_wildcards:
                patch_paths += glob.glob(os.path.join(new_patch_path_wildcard))
        else:
            patch_paths += glob.glob(os.path.join(patch_path_wildcard))
        patch_paths.sort()
        return patch_paths

    def get_hd5_paths(self):
        """Get patch paths from hd5 location that match the patch paths. Filters patch paths by values of words.

        Returns
        -------
        list of str
            List of patch paths
        """
        patch_paths_ = []
        for file in glob.glob(f"{self.hd5_location}/*.h5"):
            with h5py.File(file, "r") as f:
                patch_paths_.extend(list(f['paths']))
                # print(list(f['paths']))
        patch_paths_ = [path.decode("utf-8") for path in patch_paths_]
        patch_paths = []
        patch_path_wildcard = patch_paths_[0]
        for _ in range(len(self.patch_pattern)+1):
            patch_path_wildcard = os.path.dirname(patch_path_wildcard)
        patterns = sorted([[v, k] for k, v in self.patch_pattern.items()],
                key=lambda x: x[0])
        patterns = map(lambda x: x[1], patterns)
        for word in patterns:
            if word in self.filter_labels:
                if word=='subtype':
                    patch_path_wildcard = os.path.join(patch_path_wildcard, '**')
                else:
                    patch_path_wildcard = os.path.join(patch_path_wildcard,
                                                       self.filter_labels[word])
            else:
                patch_path_wildcard = os.path.join(patch_path_wildcard, '**')
        patch_path_wildcard = os.path.join(patch_path_wildcard, '*.png')
        if 'subtype' in self.filter_labels:
            new_patch_path_wildcards = utils.get_subtype_paths(self.filter_labels['subtype'],
                                                               self.patch_pattern,
                                                               patch_path_wildcard)
            for new_patch_path_wildcard in new_patch_path_wildcards:
                patch_paths.extend(fnmatch.filter(patch_paths_, new_patch_path_wildcard))
        else:
            patch_paths.extend(fnmatch.filter(patch_paths_, patch_path_wildcard))
        return patch_paths

    @property
    def should_use_extracted_patches(self):
        return self.load_method == 'use-extracted-patches'

    @property
    def should_use_hd5(self):
        return self.load_method == 'use-hd5'

    @property
    def should_use_manifest(self):
        return self.define_method == 'use-manifest'

    @property
    def should_use_origin(self):
        return self.define_method == 'use-origin'

    def __init__(self, config):
        """Initialize create groups component.

        Arguments
        ---------
        config : argparse.Namespace
            The args passed by user
        """
        self.seed = config.seed
        self.n_groups = config.n_groups
        self.is_binary = config.is_binary
        self.CategoryEnum = utils.create_category_enum(self.is_binary, config.subtypes)
        self.is_multiscale = config.is_multiscale
        self.patch_pattern = utils.create_patch_pattern(config.patch_pattern)
        self.filter_labels = config.filter_labels
        self.out_location = config.out_location
        self.min_patches = config.min_patches
        self.max_patches = config.max_patches
        self.balance_patches = config.balance_patches
        self.max_patient_patches = config.max_patient_patches
        # modify in code for debugging
        self.debug = False
        self.load_method = config.load_method
        self.define_method = config.define_method
        if self.should_use_extracted_patches:
            self.patch_location = config.patch_location
        elif self.should_use_hd5:
            self.hd5_location = config.hd5_location
        else:
            raise NotImplementedError(f"Load method {self.load_method} is not implemented")

        if self.should_use_manifest:
            self.manifest = utils.read_manifest(config.manifest_location)
            self.dataset_origin = list(set(self.manifest['origin']))
            self.dataset_origin = [orig.lower() for orig in self.dataset_origin]
        elif self.should_use_origin:
            self.dataset_origin = config.dataset_origin
        else:
            raise NotImplementedError(f"Define method {self.define_method} is not implemented")


    def select_patches_from_dict_as_dict(self, dict_patch, max_patches):
        """Select at most max_patches patches from dict_patch, returning the patches as a dict.
        """
        selected_patches = {k: [] for k in dict_patch.keys()}
        tmp_dict_patch = {}
        while True:
            if len(dict_patch) == 0:
                break
            num_selected_patches = sum(map(len, selected_patches.values()))
            num_patches_each_key = max(0, max_patches - \
                    num_selected_patches) // len(dict_patch)
            num_patches_each_key = min(num_patches_each_key,
                    min(map(len, dict_patch.values())))
            if num_patches_each_key < 1:
                break
            for key, patches in dict_patch.items():
                selected_patches[key].extend(patches[:num_patches_each_key])
                if len(patches[num_patches_each_key:]) > 0:
                        tmp_dict_patch[key] = patches[num_patches_each_key:]
            dict_patch = tmp_dict_patch
            tmp_dict_patch = {}
        return selected_patches

    def select_patches_from_dict(self, dict_patch, max_patches=None):
        """Select at most max_patches patches from dict_patch, or return all patches if max_patches is defined.

        Will select patches unifromly across all list in dict if max_patches is smaller than the amount of patches the patient has.

        Parameters
        ----------
        dict_patch : dict of list
            {key: [patch_path]}

        max_patches : int
            the number of patches to select from slide patches in dict_patch

        Returns
        -------
        list of str
            List of patches selecte from dict_patch
        """
        if max_patches is None:
            return list(itertools.chain.from_iterable(dict_patch.values()))
        elif sum(map(len, dict_patch.values())) <= max_patches:
            return list(itertools.chain.from_iterable(dict_patch.values()))
        else:
            selected_patches = self.select_patches_from_dict_as_dict(
                    dict_patch, max_patches)
            return list(itertools.chain.from_iterable(selected_patches.values()))

    def create_patient_subtype_patch_to_select_count(self, subtype_patient_slide_patch):
        """Produce counts of how many patches from each subtype to select for each patient.

        Balances the counts of patches to select by subtype. This is important if patient has patches that span multiple subtypes like in Tumor/Normal situations.

        Parameters
        ----------
        subtype_patient_slide_patch : dict
            {subtype: {patient: {slide_id: [patch_path]}}

        Returns
        -------
        dict
            {patient: {subtype: number of patches to select}}

        dict
            {patient: {subtype: number of patches}}
        """
        if self.max_patient_patches is None:
            raise Exception("Does not make sense to select max number of patches when self.max_patient_patches is None")
        # dict {patient: {subtype: number of patches}}
        patient_subtype_patch_count = {}
        for subtype, patient_slide_patch in subtype_patient_slide_patch.items():
            for patient, slide_patch in patient_slide_patch.items():
                num_patches = sum(map(len, slide_patch.values()))
                if patient not in patient_subtype_patch_count:
                    patient_subtype_patch_count[patient] = {}
                patient_subtype_patch_count[patient][subtype] = num_patches
        # dict {patient: {subtype: number of patches}}
        patient_subtype_patch_to_select_count = {}
        for patient, subtype_patch_count in patient_subtype_patch_count.items():
            patient_subtype_patch_to_select_count[patient] = {s: 0 for s in subtype_patch_count.keys()}
            tmp_subtype_patch_count = {}
            while True:
                if len(subtype_patch_count) == 0:
                    break
                num_patches_each_subtype = max(0, self.max_patient_patches - \
                        sum(patient_subtype_patch_to_select_count[patient].values())) \
                        // len(subtype_patch_count)
                num_patches_each_subtype = min(num_patches_each_subtype,
                        min(subtype_patch_count.values()))
                if num_patches_each_subtype < 1:
                    break
                for subtype, patch_count in subtype_patch_count.items():
                    if patch_count <= num_patches_each_subtype:
                        patient_subtype_patch_to_select_count[patient][subtype] += patch_count
                    else:
                        patient_subtype_patch_to_select_count[patient][subtype] += num_patches_each_subtype
                        tmp_subtype_patch_count[subtype] = patch_count - num_patches_each_subtype
                subtype_patch_count = tmp_subtype_patch_count
                tmp_subtype_patch_count = {}
        return patient_subtype_patch_to_select_count, patient_subtype_patch_count

    def make_groups_from_groups_subtypes(self, groups_subtypes):
        """Makes groups from groups_subtypes dict, applying patch balancing using the balance_patches parameter.

        Parameters
        ----------
        groups_subtypes : dict of (dict of list)
            Dict locator for patch paths like so {group_idx: {subtype: [patch_path]}} to select patches from.

        Returns
        -------
        dict of list
            Group data to save to group JSON file.
        """
        groups = {}
        for group_idx in range(self.n_groups):
            groups['group_' + str(group_idx + 1)] = []

        if self.balance_patches is None:
            for group_idx, groups_subtype in groups_subtypes.items():
                for patches in groups_subtype.values():
                    groups[group_idx] += patches

        elif isinstance(self.balance_patches, str):
            if self.balance_patches == 'overall':
                num_patches_to_pick = min(map(lambda d: min(map(len, d.values())),
                        groups_subtypes.values()))
                for group_idx, group_subtypes in groups_subtypes.items():
                    for patches in group_subtypes.values():
                        groups[group_idx] += patches[:num_patches_to_pick]

            elif self.balance_patches == 'group':
                # balance each group separately
                for group_idx, group_subtypes in groups_subtypes.items():
                    num_patches_to_pick = min(map(len, group_subtypes.values()))
                    for patches in group_subtypes.values():
                        groups[group_idx] += patches[:num_patches_to_pick]

            elif self.balance_patches == 'category':
                subtypes_groups = utils.invert_dict_of_dict(groups_subtypes)
                for groups_patches in subtypes_groups.values():
                    num_patches_to_pick = min(map(len, groups_patches.values()))
                    for group_idx, patches in groups_patches.items():
                        groups[group_idx] += patches[:num_patches_to_pick]

            else:
                raise NotImplementedError(f"Balance type {self.balance_patches} is not implemented.")

        elif isinstance(self.balance_patches, tuple):
            if self.balance_patches[0] == 'overall':
                for group_idx, group_subtypes in groups_subtypes.items():
                    for patches in group_subtypes.values():
                        groups[group_idx] += patches[:self.balance_patches[1]]

            elif self.balance_patches[0] == 'group':
                for group_idx, group_subtypes in groups_subtypes.items():
                    groups[group_idx] += self.select_patches_from_dict(group_subtypes,
                            max_patches=self.balance_patches[1])

            elif self.balance_patches[0] == 'category':
                subtypes_groups_patches_to_select = {}
                subtypes_groups = utils.invert_dict_of_dict(groups_subtypes)
                for subtype, groups_patches in subtypes_groups.items():
                    subtypes_groups_patches_to_select[subtype] = self.select_patches_from_dict_as_dict(
                            groups_patches, self.balance_patches[1])
                for groups_patches_to_select in subtypes_groups_patches_to_select.values():
                    for group_idx, patches in groups_patches_to_select.items():
                        groups[group_idx] += patches

            else:
                raise NotImplementedError(f"Balance type {self.balance_patches[0]} is not implemented.")
        else:
            raise NotImplementedError(f"{self.balance_patches} is not implemented.")
        return groups

    def group_summary(self, groups):
        """Function to print the group summary

        Parameters
        ----------
        groups : dict
            Groups in Yiping format
        """
        subtype_names = [s.name for s in self.CategoryEnum]
        total_slide_counts = dict(
            zip(subtype_names, [0 for s in subtype_names]))
        total_patch_counts = dict(
            zip(subtype_names, [0 for s in subtype_names]))

        slide_count_set = set()
        # latex_output = ''
        markdown_patient_output = ''
        markdown_patch_output = ''
        markdown_patient_output += self.markdown_header('Patient Counts')
        markdown_patch_output += self.markdown_header('Patch Counts')

        for group_id, patch_paths in groups.items():
            # patients = set()
            patients = {origin: set() for origin in self.dataset_origin}
            subtype_patient_counts = dict(
                zip(subtype_names, [0 for s in subtype_names]))
            subtype_patch_counts = dict(
                zip(subtype_names, [0 for s in subtype_names]))

            for patch_path in patch_paths:
                patch_id = utils.create_patch_id(patch_path, self.patch_pattern)
                slide_id = utils.get_slide_by_patch_id(patch_id, self.patch_pattern)
                patient_num = utils.get_patient_by_slide_id(slide_id,
                        dataset_origin=self.dataset_origin)
                # if patient_num not in patients:
                if patient_num not in patients[utils.get_origin(slide_id)]:
                    patient_subtype = utils.get_label_by_patch_id(
                            patch_id, self.patch_pattern, self.CategoryEnum,
                            is_binary=self.is_binary).name
                    subtype_patient_counts[patient_subtype] += 1

                # patients.add(patient_num)
                patients[utils.get_origin(slide_id)].add(patient_num)
                patch_subtype = utils.get_label_by_patch_id(
                        patch_id, self.patch_pattern, self.CategoryEnum,
                        is_binary=self.is_binary).name

                subtype_patch_counts[patch_subtype] += 1
                total_patch_counts[patch_subtype] += 1

                if slide_id not in slide_count_set:
                    slide_count_set.add(slide_id)
                    total_slide_counts[patch_subtype] += 1

            markdown_patient_output += self.markdown_formatter(np.asarray(
                    [subtype_patient_counts[s.name] for s in self.CategoryEnum]),
                    ' Patient in Group ' + group_id.split('_')[-1])
            markdown_patch_output += self.markdown_formatter(np.asarray(
                    [subtype_patch_counts[s.name] for s in self.CategoryEnum]),
                    ' Patch in Group ' + group_id.split('_')[-1])

        markdown_patient_output += self.markdown_formatter(np.asarray(
                [total_slide_counts[s.name] for s in self.CategoryEnum]),
                'Whole Slide Image')
        markdown_patch_output += self.markdown_formatter(np.asarray(
                [total_patch_counts[s.name] for s in self.CategoryEnum]),
                'Total')

        print(markdown_patient_output)
        print()
        print(markdown_patch_output)

    def generate_groups(self):
        """Generate groups in Yiping format

        Returns
        -------
        dict
            Groups in Yiping format

        list of str
            Slides excluded from groups
        """
        groups_subtypes = {}

        subtype_names = [s.name for s in self.CategoryEnum]
        ignored_slides = []

        for group_idx in range(self.n_groups):
            groups_subtypes['group_' + str(group_idx + 1)] = {subtype_name: [] for subtype_name in subtype_names}

        if self.should_use_extracted_patches and os.path.isdir(self.patch_location):
            patch_paths = self.get_patch_paths()
        elif self.should_use_hd5 and os.path.isdir(self.hd5_location):
            patch_paths = self.get_hd5_paths()
        else:
            raise NotImplementedError

        if len(patch_paths) == 0:
            if self.should_use_extracted_patches:
                raise Exception(f'No patches are obtained from patch_location {self.patch_location}')
            else:
                raise Exception(f'No patches are obtained from patch_location {self.hd5_location}')

        if self.should_use_origin:
            subtype_patient_slide_patch = utils.create_subtype_patient_slide_patch_dict(
                    patch_paths, self.patch_pattern, self.CategoryEnum,
                    is_binary=self.is_binary, dataset_origin=self.dataset_origin)
        else:
            subtype_patient_slide_patch = utils.create_subtype_patient_slide_patch_dict_manifest(
                    patch_paths, self.patch_pattern, self.CategoryEnum,
                    self.manifest, is_binary=self.is_binary)

        for subtype, patient_slide_patch in subtype_patient_slide_patch.items():
            for patient, slide_patch in patient_slide_patch.items():
                for slide, patch in slide_patch.items():
                    if self.min_patches and len(patch) < self.min_patches:
                        ignored_slides += ['/'.join([subtype, patient, slide])]
                    elif self.max_patches and len(patch) > self.max_patches:
                        ignored_slides += ['/'.join([subtype, patient, slide])]
                    else:
                        # shuffle to randomize occurance by patches by location in slide
                        random.seed(self.seed)
                        random.shuffle(patch)

        for ignored_slide in ignored_slides:
            ignored_slide_subtype, ignored_slide_patient_num, ignored_slide_slide_id = ignored_slide.split('/')
            del subtype_patient_slide_patch[ignored_slide_subtype][ignored_slide_patient_num][ignored_slide_slide_id]

        # dict {subtype: {origin: list of patients }}
        patient_subtype_origin_dict = dict(
            zip(subtype_names, [{} for s in subtype_names]))

        for subtype in subtype_names:
            for origin in self.dataset_origin:
                patient_subtype_origin_dict[subtype][origin]  = []
        for subtype, patients in subtype_patient_slide_patch.items():
            for patient in patients.keys():
                origin = patient[:patient.find('__')]
                patient_subtype_origin_dict[subtype][origin] += [patient]

        # dict {subtype: {origin: number of patients }}
        patient_subtype_origin_count = dict(
            zip(subtype_names, [{} for s in subtype_names]))
        for subtype in subtype_names:
            for origin in self.dataset_origin:
                count = len(patient_subtype_origin_dict[subtype][origin])
                assert count!=0, f"There is no patient for subtype -{subtype}- in origin -{origin}-"
                patient_subtype_origin_count[subtype][origin] = count

        # precompute how many patches we need from each (subtype, patient)
        patient_subtype_patch_to_select_count = None
        if self.max_patient_patches:
            patient_subtype_patch_to_select_count, patient_subtype_patch_count = self.create_patient_subtype_patch_to_select_count(
                    subtype_patient_slide_patch)
            if self.debug:
                print('patient_subtype_patch_to_select_count')
                print(json.dumps(patient_subtype_patch_to_select_count, indent=4, sort_keys=True))
                print()
                print('patient_subtype_patch_count')
                print(json.dumps(patient_subtype_patch_count, indent=4, sort_keys=True))
                print()

        for subtype_name in subtype_names:
            # randomize occurance of patients to put into which group
            random.seed(self.seed)
            for origin in self.dataset_origin:
                random.shuffle(patient_subtype_origin_dict[subtype_name][origin])
            steps = utils.find_steps(patient_subtype_origin_count[subtype_name], self.n_groups)
            for group_idx in range(self.n_groups):
                selected_patients = []
                for origin in self.dataset_origin:
                    start = sum(steps[origin][:group_idx])
                    selected_patients += patient_subtype_origin_dict[subtype_name][origin][start:start+steps[origin][group_idx]]
                for selected_patient in selected_patients:
                    if self.max_patient_patches:
                        groups_subtypes['group_' + str(group_idx + 1)][subtype_name] += self.select_patches_from_dict(
                                subtype_patient_slide_patch[subtype_name][selected_patient],
                                max_patches=patient_subtype_patch_to_select_count[selected_patient][subtype_name])
                    else:
                        groups_subtypes['group_' + str(group_idx + 1)][subtype_name] += self.select_patches_from_dict(
                                subtype_patient_slide_patch[subtype_name][selected_patient])

        # reshuffle to randomize occurance of patches by patient and slide
        for subtypes_patches in groups_subtypes.values():
            for patches in subtypes_patches.values():
                random.seed(self.seed)
                random.shuffle(patches)

        groups = self.make_groups_from_groups_subtypes(groups_subtypes)

        # reshuffle to randomize occurance of patches by subtype
        for patches in groups.values():
            random.seed(self.seed)
            random.shuffle(patches)
        # for group_idx in range(len(groups)):
        #     random.seed(self.seed)
        #     random.shuffle(groups['group_' + str(group_idx + 1)])

        return groups, ignored_slides

    def write_groups(self, groups):
        """Converts groups in Yiping format to Mitch format and writes it to
        self.out_location as a JSON file

        Parameters
        ----------
        groups : dict
            Groups in Yiping format
        """
        with open(self.out_location, 'w') as f:
            json.dump(groups, f)

    def run(self):
        groups, ignored_slides = self.generate_groups()
        groups = convert_yiping_to_mitch_format(groups)
        self.write_groups(groups)
        # self.group_summary(groups)
        group_names = {chunk['id']: f"Group {chunk['id'] + 1}"  for chunk in groups['chunks']}
        summary = self.print_group_summary(groups, group_names=group_names)
        print('Ignored Slides')
        print(ignored_slides)
        return summary
