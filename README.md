# Create Groups


### Development Information ###

```
Date Created: 22 July 2020
Last Update: 26 July 2021 by Amirali
Developer: Colin Chen
Version: 1.3
```

**Before running any experiment to be sure you are using the latest commits of all modules run the following script:**
```
(cd /projects/ovcare/classification/singularity_modules ; ./update_modules.sh --bcgsc-pass your/bcgsc/path)
```

## Usage

```
usage: app.py [-h] {from-experiment-manifest,from-arguments} ...

Splits patches to groups by patient case and saves the path to these patches in a group file (i.e. /path/to/patient_groups.json).
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
 (3) --max_patient_patches is applied before --balance_patches if both flags are set

positional arguments:
  {from-experiment-manifest,from-arguments}
                        Choose whether to use arguments from experiment manifest or from commandline
    from-experiment-manifest
                        Use experiment manifest

    from-arguments      Use arguments

optional arguments:
  -h, --help            show this help message and exit

usage: app.py from-experiment-manifest [-h] [--component_id COMPONENT_ID]
                                       experiment_manifest_location

positional arguments:
  experiment_manifest_location

optional arguments:
  -h, --help            show this help message and exit

  --component_id COMPONENT_ID

usage: app.py from-arguments [-h] [--seed SEED] [--n_groups N_GROUPS]
                             [--subtypes SUBTYPES [SUBTYPES ...]]
                             [--is_binary] [--is_multiscale]
                             [--balance_patches BALANCE_PATCHES]
                             [--patch_pattern PATCH_PATTERN]
                             [--filter_labels FILTER_LABELS [FILTER_LABELS ...]]
                             --out_location OUT_LOCATION
                             [--min_patches MIN_PATCHES]
                             [--max_patches MAX_PATCHES]
                             [--max_patient_patches MAX_PATIENT_PATCHES]
                             {use-extracted-patches,use-hd5} ...

positional arguments:
  {use-extracted-patches,use-hd5}
                        Specify how to load patches.
                            There are 2 ways of loading patches: by use_extracted_patches and by use_hd5.
    use-extracted-patches
                        Use extracted and saved patches

    use-hd5             Use hd5 files

optional arguments:
  -h, --help            show this help message and exit

  --seed SEED           Seed for random shuffle.
                         (default: 256)

  --n_groups N_GROUPS   The number of groups in groups file.
                         (default: 3)

  --subtypes SUBTYPES [SUBTYPES ...]
                        Space separated words describing subtype=groupping pairs for this study. Example: if doing one-vs-rest on the subtypes MMRD vs P53ABN, P53WT and POLE then the input should be 'MMRD=0 P53ABN=1 P53WT=1 POLE=1'
                         (default: {'MMRD': 0, 'P53ABN': 1, 'P53WT': 2, 'POLE': 3})

  --is_binary           Whether we want to categorize patches by the Tumor/Normal category (true) or by the subtype category (false).
                         (default: False)

  --is_multiscale       Whether patches have multiple scales i.e. different magnifications. Not currently used.
                         (default: False)

  --balance_patches BALANCE_PATCHES
                        Optional method to balance patches. Can choose (1) ('group', 'overall', 'category') or (2) one of ('group=cap_amt', 'overall=cap_amt', 'category=cap_amt').In the case (1), we will balance out the patches in every group, category, or overall (see description for more details). In case (2), we will cap the number of patches in every group, category, or overall to the number cap_amt.
                         (default: None)

  --patch_pattern PATCH_PATTERN
                        '/' separated words describing the directory structure of the patch paths. The words are ('annotation', 'subtype', 'slide', 'patch_size', 'magnification'). A non-multiscale patch can be contained in a directory /path/to/patch/rootdir/Tumor/MMRD/VOA-1234/1_2.png so its patch_pattern is annotation/subtype/slide. A multiscale patch can be contained in a directory /path/to/patch/rootdir/Stroma/P53ABN/VOA-1234/10/3_400.png so its patch_pattern is annotation/subtype/slide/magnification
                         (default: annotation/subtype/slide)

  --filter_labels FILTER_LABELS [FILTER_LABELS ...]
                        Space separated words describing label=value pairs to filter patch by label value. For example, if a dataset contains patche paths like path/to/patch/rootdir/Tumor/MMRD/VOA-1234/256/20/1_2.png and we want to select Tumor patches of pixel size 256 * 256 and 20x magnification then the patch_pattern is annotation/subtype/slide/patch_size/magnification and the select_labels is 'annotation=Tumor patch_size=256 magnification=20'
                         (default: {})

  --out_location OUT_LOCATION
                        full path of the groups file (i.e. /path/to/patient_groups.json). An example is '/projects/ovcare/classification/cchen/ml/data/local_ec_100/patient_groups.json'
                         (default: None)

  --min_patches MIN_PATCHES
                        Only include from slides that have at least min_patches number of patches
                         (default: None)

  --max_patches MAX_PATCHES
                        Only include from slides that have at most max_patches number of patches
                         (default: None)

  --max_patient_patches MAX_PATIENT_PATCHES
                        Select at most max_patient_patches number of patches from each patient.
                         (default: None)

usage: app.py from-arguments use-extracted-patches [-h] --patch_location
                                                   PATCH_LOCATION
                                                   {use-manifest,use-origin}
                                                   ...

positional arguments:
  {use-manifest,use-origin}
                        Specify how to define patient ID and slide ID:
                                1. use-manifest 2. origin
    use-manifest        Use manifest file to locate slides.
                                a CSV file with minimum of 4 column and maximum of 6 columns. The name of columns
                                should be among ['origin', 'patient_id', 'slide_id', 'slide_path', 'annotation_path', 'subtype'].
                                origin, slide_id, patient_id must be one of the columns.

    use-origin          Use origin for detecting patient ID and slide ID.
                                NOTE: It only works for German, OVCARE, and TCGA.

optional arguments:
  -h, --help            show this help message and exit

  --patch_location PATCH_LOCATION
                        root directory of all patches of a study. The patch directory structure is '/patch_location/patch_pattern/x_y.png'. See --patch_pattern below. An example is '/projects/ovcare/classification/cchen/ml/data/local_ec_100/patches_256_sorted'
                         (default: None)

usage: app.py from-arguments use-extracted-patches use-manifest
       [-h] --manifest_location MANIFEST_LOCATION

optional arguments:
  -h, --help            show this help message and exit

  --manifest_location MANIFEST_LOCATION
                        Path to manifest CSV file.
                         (default: None)

usage: app.py from-arguments use-extracted-patches use-origin
       [-h] [--dataset_origin DATASET_ORIGIN [DATASET_ORIGIN ...]]

optional arguments:
  -h, --help            show this help message and exit

  --dataset_origin DATASET_ORIGIN [DATASET_ORIGIN ...]
                        List of the origins of the slide dataset the patches are generated from. Should be from ('ovcare', 'tcga', 'german', 'other'). (For multiple origins, works for TCGA+ovcare. Mix of Other origins must be tested.)
                         (default: ['ovcare'])

usage: app.py from-arguments use-hd5 [-h] --hd5_location HD5_LOCATION
                                     {use-manifest,use-origin} ...

positional arguments:
  {use-manifest,use-origin}
                        Specify how to define patient ID and slide ID:
                                1. use-manifest 2. origin
    use-manifest        Use manifest file to locate slides.
                                a CSV file with minimum of 4 column and maximum of 6 columns. The name of columns
                                should be among ['origin', 'patient_id', 'slide_id', 'slide_path', 'annotation_path', 'subtype'].
                                origin, slide_id, patient_id must be one of the columns.

    use-origin          Use origin for detecting patient ID and slide ID.
                                NOTE: It only works for German, OVCARE, and TCGA.

optional arguments:
  -h, --help            show this help message and exit

  --hd5_location HD5_LOCATION
                        root directory of all hd5 of a study.
                         (default: None)

usage: app.py from-arguments use-hd5 use-manifest [-h] --manifest_location
                                                  MANIFEST_LOCATION

optional arguments:
  -h, --help            show this help message and exit

  --manifest_location MANIFEST_LOCATION
                        Path to manifest CSV file.
                         (default: None)

usage: app.py from-arguments use-hd5 use-origin [-h]
                                                [--dataset_origin DATASET_ORIGIN [DATASET_ORIGIN ...]]

optional arguments:
  -h, --help            show this help message and exit

  --dataset_origin DATASET_ORIGIN [DATASET_ORIGIN ...]
                        List of the origins of the slide dataset the patches are generated from. Should be from ('ovcare', 'tcga', 'german', 'other'). (For multiple origins, works for TCGA+ovcare. Mix of Other origins must be tested.)
                         (default: ['ovcare'])

```
TODO: there is a chance --balance_patches sets empty groups. This happens if any patches for some (group, category) is zero.
TODO: in create_groups, variables are named 'subtype' instead of 'category'. That leads to confusion.
TODO: further explain how --max_patient_patches works in description.
TODO: make GroupCreator.group_summary() return DataFrame. Test against DataFrame output.

