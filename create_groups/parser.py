import argparse

from submodule_utils import (BALANCE_PATCHES_OPTIONS, DATASET_ORIGINS,
        PATCH_PATTERN_WORDS, set_random_seed, DEAFULT_SEED)
from submodule_utils.manifest.arguments import manifest_arguments
from submodule_utils.arguments import (
        AIMArgumentParser,
        dir_path, file_path, dataset_origin, balance_patches_options,
        str_kv, int_kv, subtype_kv, make_dict,
        ParseKVToDictAction, CustomHelpFormatter)
from create_groups import *

description="""Splits patches to groups by patient case and saves the path to these patches in a group file (i.e. /path/to/patient_groups.json).
The patient_groups.json file uses Mitch's format for groups i.e. it is a json file with the format

{
    "chunks": [
        {
            "id": int,
            "imgs": list of paths to patches
        },
        ...DEAFULT_SEEDE || Total ||
|  Patient in Group 1 | 9 | 13 | 20 | 3 | 45 |
|  Patient in Group 2 | 9 | 13 | 20 | 3 | 45 |
|  Patient in Group 3 | 8 | 13 | 20 | 3 | 44 |
| Whole Slide Image | 38 | 63 | 79 | 13 | 193 |


|| Patch Counts || MMRD || P53ABN || P53WT || POLE || Total ||
|  Patch in Group 1 | 38659 | 43918 | 52645 | 1791 | 137013 |
|  Patch in Group 2 | 15261 | 71059 | 34979 | 17248 | 138547 |
|  Patch in Group 3 | 19431 | 51330 | 53700 | 7881 | 132342 |
| Total | 73351 | 166307 | 141324 | 26920 | 407902 |

What are **categories**?

1) if the --is_binary flag is used, then categories=('Tumor', 'Normal') where 'Tumor' is any patch annotated as 'Tumor' and 'Normal' is any patch with annotated as 'Other', 'MucinousBorderlineTumor', 'Necrosis' or 'Stroma'
2) if the --is_binary flag is not used, then categories=subtype (i.e. CC, EC, MC, LGSC, HGSC)

**balance_patches**:

The --balance_patches flag gives the following options (illustrated):

1) `--balance_patches overall` sets every cell to the min cell.
DEAFULT_SEEDll to the min cell in each group.

|| Patch Counts || MMRD || P53ABN || P53WT || POLE || Total ||
|  Patch in Group 1 | 1791 | 1791 | 1791 | 1791 | 7164 |
|  Patch in Group 2 | 15261 | 15261 | 15261 | 15261 | 61044 |
|  Patch in Group 3 | 7881 | 7881 | 7881 | 7881 | 31524 |
| Total | 24933 | 24933 | 24933 | 24933 | 99732 |
set_random_seedup 1 | 30000 | 30000 | 30000 | 1791 | 91791 |
|  Patch in Group 2 | 15261 | 30000 | 30000 | 17248 | 92509 |
|  Patch in Group 3 | 19431 | 30000 | 30000 | 7881 | 87312 |
| Total | 64692 | 90000 | 90000 | 26920 | 271612 |

3) `--balance_patches group=cap_amt` caps the number of patches in every group by cap_amt.
`--balance_patches group=135000`

|| Patch Counts || MMRD || P53ABN || P53WT || POLE || Total ||
|  Patch in Group 1 | 38659 | 43918 | 50632 | 1791 | 135000 |
|  Patch in Group 2 | 15261 | 67512 | 34979 | 17248 | 135000 |
|  Patch in Group 3 | 19431 | 51330 | 53700 | 7881 | 132342 |
| Total | 73351 | 162760 | 139311 | 26920 | 402342 |

3) `--balance_patches category=cap_amt` caps the number of patches in every category by cap_amt.
`--balance_patches category=100000`

|| Patch Counts || MMRD || P53ABN || P53WT || POLE || Total ||
|  Patch in Group 1 | 38659 | 33333 | 33333 | 1791 | 107116 |
|  Patch in Group 2 | 15261 | 33333 | 33333 | 17248 | 99175 |
|  Patch in Group 3 | 19431 | 33333 | 33333 | 7881 | 93978 |
| Total | 73351 | 99999 | 99999 | 26920 | 300269 |

**max_patient_patches**:

If --max_patient_patches is set, then we will select max_patient_patches from each patient case, so if max_patient_patches=60 then we will select at most 60 patches across all slides belonging to the patient.

 (1) this will select patches uniformly across all slides belonging to the patient. For example if there are 3 slides, then we will sample 20 patches from each slide unless a few slides have <20 patches in which case we select >20 patches from the slides with enough patches until we have 60 in total.
 (2) this will select patches uniformly across all categories belonging to the patient. For example if categories=('Tumor', 'Normal') then we will select 30 patches each category unless one category has <30 slides in which case we select we select >30 patches in the other category until we have 60 in total.
 (3) --max_patient_patches is applied before --balance_patches if both flags are set"""

# epilog="""
# TODO: there is a chance --balance_patches sets empty groups. This happens if any patches for some (group, category) is zero.
# TODO: in create_groups, variables are named 'subtype' instead of 'category'. That leads to confusion.
# TODO: further explain how --max_patient_patches works in description
# TODO: make GroupCreator.group_summary() return DataFrame. Test against DataFrame output
# """
epilog=""

@manifest_arguments(description=description, epilog=epilog,
        default_component_id=default_component_id)
def create_parser(parser):
    parser.add_argument("--seed", type=int, default=DEAFULT_SEED,
            help="Seed for random shuffle.")

    parser.add_argument("--n_groups", type=int, default=default_n_groups,
            help="The number of groups in groups file.")

    parser.add_argument("--subtypes", nargs='+', type=subtype_kv,
            action=ParseKVToDictAction, default=default_subtypes,
            help="Space separated words describing subtype=groupping pairs for this study. "
            "Example: if doing one-vs-rest on the subtypes MMRD vs P53ABN, P53WT and POLE then "
            "the input should be 'MMRD=0 P53ABN=1 P53WT=1 POLE=1'")

    parser.add_argument("--is_binary", action='store_true',
            help="Whether we want to categorize patches by the Tumor/Normal category (true) "
            "or by the subtype category (false).")

    parser.add_argument("--is_multiscale", action='store_true',
            help="Whether patches have multiple scales i.e. different magnifications. "
            "Not currently used.")

    parser.add_argument("--balance_patches", type=balance_patches_options, required=False,
            help="Optional method to balance patches. "
            f"Can choose (1) {tuple(BALANCE_PATCHES_OPTIONS)} "
            f"or (2) one of {tuple(f'{o}=cap_amt' for o in BALANCE_PATCHES_OPTIONS)}."
            "In the case (1), we will balance out the patches in every group, category, or overall "
            "(see description for more details). In case (2), we will cap the number of patches in "
            "every group, category, or overall to the number cap_amt.")

    parser.add_argument("--patch_pattern", type=str,
            default=default_patch_pattern,
            help="'/' separated words describing the directory structure of the "
            f"patch paths. The words are {tuple(PATCH_PATTERN_WORDS)}. "
            "A non-multiscale patch can be contained in a directory "
            "/path/to/patch/rootdir/Tumor/MMRD/VOA-1234/1_2.png so its patch_pattern is "
            "annotation/subtype/slide. A multiscale patch can be contained in a "
            "directory /path/to/patch/rootdir/Stroma/P53ABN/VOA-1234/10/3_400.png so "
            "its patch_pattern is annotation/subtype/slide/magnification")

    parser.add_argument("--filter_labels", nargs='+', type=str_kv,
            action=ParseKVToDictAction, default=default_filter_labels,
            help="Space separated words describing label=value pairs to filter patch "
            "by label value. For example, if a dataset contains patche paths like "
            "path/to/patch/rootdir/Tumor/MMRD/VOA-1234/256/20/1_2.png and we want to "
            "select Tumor patches of pixel size 256 * 256 and 20x magnification then "
            "the patch_pattern is annotation/subtype/slide/patch_size/magnification "
            "and the select_labels is 'annotation=Tumor patch_size=256 "
            "magnification=20'")

    parser.add_argument("--out_location", type=str, required=True,
            help="full path of the groups file (i.e. /path/to/patient_groups.json). An "
            "example is '/projects/ovcare/classification/cchen/ml/data/local_ec_100/patient_groups.json'")

    parser.add_argument("--min_patches", type=int, required=False,
            help="Only include from slides that have at least min_patches number of patches")

    parser.add_argument("--max_patches", type=int, required=False,
            help="Only include from slides that have at most max_patches number of patches")

    parser.add_argument("--max_patient_patches", type=int, required=False,
            help="Select at most max_patient_patches number of patches from each patient.")

    help_subparsers_load = """Specify how to load patches.
    There are 2 ways of loading patches: by use_extracted_patches and by use_hd5."""
    subparsers_load = parser.add_subparsers(dest='load_method',
            required=True,
            parser_class=AIMArgumentParser,
            help=help_subparsers_load)

    help_extracted_patches = """Use extracted and saved patches"""
    parser_manifest = subparsers_load.add_parser("use-extracted-patches",
            help=help_extracted_patches)

    parser_manifest.add_argument("--patch_location", type=dir_path, required=True,
            help="root directory of all patches of a study. The patch directory structure is "
            "'/patch_location/patch_pattern/x_y.png'. See --patch_pattern below. An example is "
            "'/projects/ovcare/classification/cchen/ml/data/local_ec_100/patches_256_sorted'")

    help_hd5 = """Use hd5 files"""
    parser_hd5 = subparsers_load.add_parser("use-hd5",
            help=help_hd5)

    parser_hd5.add_argument("--hd5_location", type=dir_path, required=True,
            help="root directory of all hd5 of a study.")

    subparsers_load_list = [parser_manifest, parser_hd5]

    for subparser in subparsers_load_list:
        help_subparsers_define = """Specify how to define patient ID and slide ID:
        1. use-manifest 2. origin"""
        subparsers_define = subparser.add_subparsers(dest="define_method",
                required=True,
                parser_class=AIMArgumentParser,
                help=help_subparsers_define)

        help_manifest_ = """Use manifest file to locate slides.
        a CSV file with minimum of 4 column and maximum of 6 columns. The name of columns
        should be among ['origin', 'patient_id', 'slide_id', 'slide_path', 'annotation_path', 'subtype'].
        origin, slide_id, patient_id must be one of the columns."""

        parser_manifest_ = subparsers_define.add_parser("use-manifest",
                help=help_manifest_)
        parser_manifest_.add_argument("--manifest_location", type=file_path, required=True,
                help="Path to manifest CSV file.")

        help_origin = """Use origin for detecting patient ID and slide ID.
        NOTE: It only works for German, OVCARE, and TCGA."""

        parser_origin = subparsers_define.add_parser("use-origin",
                help=help_origin)
        parser_origin.add_argument('--dataset_origin', type=dataset_origin, nargs='+',
                default=default_dataset_origin,
                help="List of the origins of the slide dataset the patches are generated from. "
                f"Should be from {tuple(DATASET_ORIGINS)}. "
                "(For multiple origins, works for TCGA+ovcare. Mix of Other origins must be tested.)")


def get_args():
        parser = create_parser()
        args = parser.get_args()
        set_random_seed(args.seed)
        return args
