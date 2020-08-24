import pytest
import random
import itertools

import submodule_utils as utils
from create_groups.tests import (OUTPUT_DIR, GROUP_PATH, MOCK_PATCH_DIR)
from create_groups.parser import create_parser
from create_groups import *
random.seed(default_seed)

def generate_str(ll):
    out = ll[0].copy()
    for idx in range(1, len(ll)):
        tmp = []
        for s in out:
            tmp.extend([s + t for t in ll[idx]])
        out = tmp
    return out

def generate_lists(ll):
    if not ll:
        return [ ]
    out = [[s] for s in ll[0]]
    for idx in range(1, len(ll)):
        tmp = [ ]
        for l in out:
            tmp.extend([l + [t] for t in ll[idx]])
        out = tmp
    return out

def test_run_binary(clean_output):
    """
    TODO: make GroupCreator.group_summary() return DataFrame. Test against DataFrame output
    """
    is_binary = True
    patch_pattern = 'annotation/subtype/slide/patch_size/magnification'
    filter_labels = {'patch_size': '512', 'magnification': '10'}
    args_str = f"""
    from-arguments
    --patch_location {MOCK_PATCH_DIR}
    --patch_pattern {patch_pattern}
    --out_location {GROUP_PATH}
    --filter_labels {utils.dict_to_space_sep_eql(filter_labels)}
    --is_binary
    """
    # should get 1728
    parser = create_parser()
    config = parser.get_args(args_str.split())
    gc = GroupCreator(config)
    summary = gc.run()
    with open(GROUP_PATH, 'r') as f:
        actual = json.load(f)
    actual = utils.map_to_list(lambda g: g['imgs'], actual['chunks'])
    """Check patch grouping by patients"""
    patients = utils.map_to_list(lambda v: map(lambda s: s.split('/')[6], v), actual)
    patients = utils.map_to_list(lambda v: set(v), patients)
    for patient_set in patients:
        assert patient_set <= set(['VOA-100', 'VOA-200', 'VOA-300'])
    for patient_set_1, patient_set_2 in itertools.combinations(patients, 2):
        assert patient_set_1.isdisjoint(patient_set_2)
    """check that there are no duplicates within each group."""
    counts_dup = utils.map_to_list(len, actual)
    actual = utils.map_to_list(set, actual)
    counts_dedup = utils.map_to_list(len, actual)
    assert counts_dup == counts_dedup
    """check that there are no duplicates across groups."""
    count_dup = sum(counts_dedup)
    actual = list(utils.merge_sets(actual))
    count_dup = sum(counts_dedup)
    count_dedup = len(actual)
    assert count_dup == count_dedup
    assert count_dedup == 192
    """check the paths in the group"""
    expected = generate_lists([
        ['create_groups/tests/mock/patches'],
        ['Tumor', 'Stroma', 'Necrosis', 'Other'],
        ['MMRd', 'p53abn', 'p53wt', 'POLE'],
        ['VOA-100', 'VOA-200', 'VOA-300'],
        ['512/10'],
        ['100_100.png', '100_200.png', '200_100.png', '200_200.png']
    ])
    expected = utils.map_to_list('/'.join, expected)
    actual.sort()
    expected.sort()
    assert actual == expected
    # TODO: test summary

def test_run_subtypes(clean_output):
    """
    TODO: make GroupCreator.group_summary() return DataFrame. Test against DataFrame output
    """
    subtypes = {'MMRd': 1, 'p53abn': 2, 'p53wt': 3, 'POLE': 4}
    patch_pattern = 'annotation/subtype/slide/patch_size/magnification'
    filter_labels = {'patch_size': '512', 'magnification': '10'}
    args_str = f"""
    from-arguments
    --subtypes {utils.dict_to_space_sep_eql(subtypes)}
    --patch_location {MOCK_PATCH_DIR}
    --patch_pattern {patch_pattern}
    --out_location {GROUP_PATH}
    --filter_labels {utils.dict_to_space_sep_eql(filter_labels)}
    """
    # should get 1728
    parser = create_parser()
    config = parser.get_args(args_str.split())
    gc = GroupCreator(config)
    summary = gc.run()
    with open(GROUP_PATH, 'r') as f:
        actual = json.load(f)
    actual = utils.map_to_list(lambda g: g['imgs'], actual['chunks'])
    """Check patch grouping by patients"""
    patients = utils.map_to_list(lambda v: map(lambda s: s.split('/')[6], v), actual)
    patients = utils.map_to_list(lambda v: set(v), patients)
    for patient_set in patients:
        assert patient_set <= set(['VOA-100', 'VOA-200', 'VOA-300'])
    for patient_set_1, patient_set_2 in itertools.combinations(patients, 2):
        assert patient_set_1.isdisjoint(patient_set_2)
    """check that there are no duplicates within each group."""
    counts_dup = utils.map_to_list(len, actual)
    actual = utils.map_to_list(set, actual)
    counts_dedup = utils.map_to_list(len, actual)
    assert counts_dup == counts_dedup
    """check that there are no duplicates across groups."""
    count_dup = sum(counts_dedup)
    actual = list(utils.merge_sets(actual))
    count_dup = sum(counts_dedup)
    count_dedup = len(actual)
    assert count_dup == count_dedup
    assert count_dedup == 192
    """check the paths in the group"""
    expected = generate_lists([
        ['create_groups/tests/mock/patches'],
        ['Tumor', 'Stroma', 'Necrosis', 'Other'],
        ['MMRd', 'p53abn', 'p53wt', 'POLE'],
        ['VOA-100', 'VOA-200', 'VOA-300'],
        ['512/10'],
        ['100_100.png', '100_200.png', '200_100.png', '200_200.png']
    ])
    expected = utils.map_to_list('/'.join, expected)
    actual.sort()
    expected.sort()
    assert actual == expected
    # TODO: test summary