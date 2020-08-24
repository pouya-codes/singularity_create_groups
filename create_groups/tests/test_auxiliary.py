import pytest
import random

import submodule_utils as utils
from create_groups.tests import (OUTPUT_DIR, MOCK_PATCH_DIR)
from create_groups.parser import create_parser
from create_groups import *
random.seed(default_seed)

def test_parse_args_1():
    subtypes = {'MMRd': 1, 'Other': 0, 'p53abn': 0, 'p53wt': 0, 'POLE': 0}
    args_str = f"""
    from-arguments
    --patch_location {MOCK_PATCH_DIR}
    --out_location {OUTPUT_DIR}
    --subtypes {utils.dict_to_space_sep_eql(subtypes)}
    """
    parser = create_parser()
    config = parser.get_args(args_str.split())
    gc = GroupCreator(config)
    assert gc.seed == default_seed
    assert gc.n_groups == default_n_groups
    assert gc.is_binary == False
    assert gc.is_multiscale == False
    assert gc.dataset_origin == default_dataset_origin
    assert gc.patch_location == MOCK_PATCH_DIR
    assert gc.patch_pattern == utils.create_patch_pattern(default_patch_pattern)
    assert gc.filter_labels == {}
    assert gc.out_location == OUTPUT_DIR
    assert gc.min_patches == None
    assert gc.max_patches == None
    assert gc.balance_patches == None
    assert gc.max_patient_patches == None
    assert {c.name: c.value for c in gc.CategoryEnum} == {'MMRD': 1, 'OTHER': 0}

def test_parse_args_2():
    subtypes = {'MMRd': 1, 'Other': 0, 'p53abn': 0, 'p53wt': 0, 'POLE': 0}
    args_str = f"""
    from-arguments
    --patch_location {MOCK_PATCH_DIR}
    --out_location {OUTPUT_DIR}
    --subtypes {utils.dict_to_space_sep_eql(subtypes)}
    --is_binary
    """
    parser = create_parser()
    config = parser.get_args(args_str.split())
    gc = GroupCreator(config)
    assert gc.is_binary == True
    assert {c.name: c.value for c in gc.CategoryEnum} == {'Tumor': 1, 'Normal': 0}

def test_get_patch_paths_1():
    """Test GroupCreator.get_patch_paths() gets all paths when no filter is applied.
    """
    patch_pattern = 'annotation/subtype/slide/patch_size/magnification'
    args_str = f"""
    from-arguments
    --patch_location {MOCK_PATCH_DIR}
    --patch_pattern {patch_pattern}
    --out_location {OUTPUT_DIR}
    --is_binary
    """
    parser = create_parser()
    config = parser.get_args(args_str.split())
    gc = GroupCreator(config)
    assert gc.patch_location == MOCK_PATCH_DIR
    assert gc.patch_pattern == utils.create_patch_pattern(patch_pattern)
    assert gc.is_binary == True
    assert {c.name: c.value for c in gc.CategoryEnum} == {'Tumor': 1, 'Normal': 0}
    patch_paths = gc.get_patch_paths()
    assert len(patch_paths) == 1728

def test_get_patch_paths_2():
    """Test GroupCreator.get_patch_paths() filters patches
    """
    is_binary = True
    patch_pattern = 'annotation/subtype/slide/patch_size/magnification'
    filter_labels = {'patch_size': '256', 'magnification': '10', 'annotation': 'Tumor'}
    args_str = f"""
    from-arguments
    --patch_location {MOCK_PATCH_DIR}
    --patch_pattern {patch_pattern}
    --out_location {OUTPUT_DIR}
    --is_binary
    --filter_labels {utils.dict_to_space_sep_eql(filter_labels)}
    """
    parser = create_parser()
    config = parser.get_args(args_str.split())
    gc = GroupCreator(config)
    assert gc.filter_labels == filter_labels
    patch_paths = gc.get_patch_paths()
    patch_pattern = utils.create_patch_pattern(patch_pattern)
    CategoryEnum = utils.create_category_enum(is_binary)
    assert len(patch_paths) == 48
    for patch_path in patch_paths:
        patch_id = utils.create_patch_id(patch_path, patch_pattern)
        label = utils.get_label_by_patch_id(patch_id, patch_pattern, CategoryEnum,
                is_binary=is_binary).name
        patch_size = utils.get_patch_size_by_patch_id(patch_id, patch_pattern)
        patch_mag = utils.get_magnification_by_patch_id(patch_id, patch_pattern)
        assert patch_size == 256
        assert patch_mag == 10
        assert label == 'Tumor'

def test_get_patch_paths_3():
    is_binary = True
    patch_pattern = 'annotation/subtype/slide/patch_size/magnification'
    filter_labels = {'patch_size': '512', 'magnification': '10'}
    args_str = f"""
    from-arguments
    --patch_location {MOCK_PATCH_DIR}
    --patch_pattern {patch_pattern}
    --out_location {OUTPUT_DIR}
    --is_binary
    --filter_labels {utils.dict_to_space_sep_eql(filter_labels)}
    """
    parser = create_parser()
    config = parser.get_args(args_str.split())
    gc = GroupCreator(config)
    assert gc.filter_labels == filter_labels
    patch_paths = gc.get_patch_paths()
    patch_pattern = utils.create_patch_pattern(patch_pattern)
    # CategoryEnum = utils.create_category_enum(is_binary)
    assert len(patch_paths) == 192
    for patch_path in patch_paths:
        patch_id = utils.create_patch_id(patch_path, patch_pattern)
        patch_size = utils.get_patch_size_by_patch_id(patch_id, patch_pattern)
        patch_mag = utils.get_magnification_by_patch_id(patch_id, patch_pattern)
        assert patch_size == 512
        assert patch_mag == 10

def test_get_patch_paths_4():
    is_binary = False
    filter_labels = {'subtype': 'p53abn'}
    patch_pattern = 'annotation/subtype/slide/patch_size/magnification'
    args_str = f"""
    from-arguments
    --patch_location {MOCK_PATCH_DIR}
    --patch_pattern {patch_pattern}
    --out_location {OUTPUT_DIR}
    --is_binary
    --filter_labels {utils.dict_to_space_sep_eql(filter_labels)}
    """
    parser = create_parser()
    config = parser.get_args(args_str.split())
    gc = GroupCreator(config)
    assert gc.filter_labels == filter_labels
    patch_paths = gc.get_patch_paths()
    patch_pattern = utils.create_patch_pattern(patch_pattern)
    CategoryEnum = utils.create_category_enum(is_binary, subtypes=default_subtypes)
    assert len(patch_paths) == 432
    for patch_path in patch_paths:
        patch_id = utils.create_patch_id(patch_path, patch_pattern)
        label = utils.get_label_by_patch_id(patch_id, patch_pattern, CategoryEnum,
                is_binary=is_binary).name
        assert label == 'P53ABN'

def test_select_patches_from_patient_1():
    args_str = f"""
    from-arguments
    --patch_location {MOCK_PATCH_DIR}
    --out_location {OUTPUT_DIR}
    --is_binary
    """
    parser = create_parser()
    config = parser.get_args(args_str.split())
    gc = GroupCreator(config)
    slide_patch = {
        'VOA-1000A': [
            "/VOA-1000A/1"
        ],
        'VOA-1000B': [
            "/VOA-1000B/1", "/VOA-1000B/2"
        ],
        'VOA-1000C': [
            "VOA-1000C/1", "VOA-1000C/2", "VOA-1000C/3"
        ]
    }
    actual = gc.select_patches_from_dict(slide_patch, max_patches=5)
    expected = ["/VOA-1000A/1", "/VOA-1000B/1", "/VOA-1000B/2",  "VOA-1000C/1",
            "VOA-1000C/2"]
    assert sorted(actual) == sorted(expected)
    actual = gc.select_patches_from_dict(slide_patch, max_patches=6)
    expected = []
    for patches in slide_patch.values():
        expected.extend(patches)
    assert sorted(actual) == sorted(expected)

def test_select_patches_from_patient_2():
    args_str = f"""
    from-arguments
    --patch_location {MOCK_PATCH_DIR}
    --out_location {OUTPUT_DIR}
    --is_binary
    """
    parser = create_parser()
    config = parser.get_args(args_str.split())
    gc = GroupCreator(config)
    slide_patch = {
        'VOA-1000A': [
            "/VOA-1000A/1"
        ],
        'VOA-1000B': [
            "/VOA-1000B/1", "/VOA-1000B/2"
        ],
        'VOA-1000C': [
            "VOA-1000C/1", "VOA-1000C/2", "VOA-1000C/3"
        ],
        'VOA-1000D': [
            "VOA-1000D/1", "VOA-1000D/2", "VOA-1000D/3", "VOA-1000D/4"
        ],
        'VOA-1000E': [
            "VOA-1000E/1", "VOA-1000E/2", "VOA-1000E/3", "VOA-1000E/4"
        ]
    }
    actual = gc.select_patches_from_dict(slide_patch, max_patches=12)
    expected = ['/VOA-1000A/1', '/VOA-1000B/1', 'VOA-1000C/1', 'VOA-1000D/1',
            'VOA-1000E/1', '/VOA-1000B/2', 'VOA-1000C/2', 'VOA-1000D/2',
            'VOA-1000E/2', 'VOA-1000C/3', 'VOA-1000D/3', 'VOA-1000E/3']
    assert sorted(actual) == sorted(expected)
    actual = gc.select_patches_from_dict(slide_patch, max_patches=9)
    expected = ['/VOA-1000A/1', '/VOA-1000B/1', 'VOA-1000C/1', 'VOA-1000D/1',
            'VOA-1000E/1', '/VOA-1000B/2', 'VOA-1000C/2', 'VOA-1000D/2',
            'VOA-1000E/2']
    assert sorted(actual) == sorted(expected)
    actual = gc.select_patches_from_dict(slide_patch, max_patches=10)
    assert sorted(actual) == sorted(expected)
    actual = gc.select_patches_from_dict(slide_patch, max_patches=11)
    assert sorted(actual) == sorted(expected)
    actual = gc.select_patches_from_dict(slide_patch, max_patches=20)
    expected = []
    for patches in slide_patch.values():
        expected.extend(patches)
    assert sorted(actual) == sorted(expected)
    actual = gc.select_patches_from_dict(slide_patch)
    assert sorted(actual) == sorted(expected)

def test_select_patches_from_patient_3():
    args_str = f"""
    from-arguments
    --patch_location {MOCK_PATCH_DIR}
    --out_location {OUTPUT_DIR}
    --is_binary
    """
    parser = create_parser()
    config = parser.get_args(args_str.split())
    gc = GroupCreator(config)
    slide_patch = {
        'VOA-1000A': [
            "/VOA-1000A/1", "/VOA-1000A/2"
        ],
        'VOA-1000B': [
            "/VOA-1000B/1", "/VOA-1000B/2", "/VOA-1000B/3",
            "/VOA-1000B/4", "/VOA-1000B/5", "/VOA-1000B/6"
        ],
        'VOA-1000C': [
            "/VOA-1000C/1", "/VOA-1000C/2", "/VOA-1000C/3",
            "/VOA-1000C/4", "/VOA-1000C/5", "/VOA-1000C/6"
        ],
        'VOA-1000D': [
            "/VOA-1000D/1", "/VOA-1000D/2", "/VOA-1000D/3",
            "/VOA-1000D/4", "/VOA-1000D/5", "/VOA-1000D/6"
        ]
    }
    actual = gc.select_patches_from_dict(slide_patch, max_patches=15)
    expected = ['/VOA-1000A/1', '/VOA-1000A/2', '/VOA-1000B/1', '/VOA-1000B/2',
            '/VOA-1000C/1', '/VOA-1000C/2', '/VOA-1000D/1', '/VOA-1000D/2',
            '/VOA-1000B/3', '/VOA-1000B/4', '/VOA-1000C/3', '/VOA-1000C/4',
            '/VOA-1000D/3', '/VOA-1000D/4']
    assert sorted(actual) == sorted(expected)

def test_create_patient_subtype_patch_to_select_count_1():
    args_str = f"""
    from-arguments
    --patch_location {MOCK_PATCH_DIR}
    --out_location {OUTPUT_DIR}
    --is_binary
    --max_patient_patches 6
    """
    parser = create_parser()
    config = parser.get_args(args_str.split())
    gc = GroupCreator(config)
    assert gc.max_patient_patches == 6
    subtype_patient_slide_patch = {
        'Tumor': {
            # Mainly Tumor with Tumor > max_patient_patches
            'VOA-1000': {
                'VOA-1000A': ['/Tumor/VOA-1000A/1', '/Tumor/VOA-1000A/2', '/Tumor/VOA-1000A/3'],
                'VOA-1000B': ['/Tumor/VOA-1000B/1', '/Tumor/VOA-1000B/2'],
                'VOA-1000C': ['/Tumor/VOA-1000C/1', '/Tumor/VOA-1000C/2'],
            },
            # Balanced with each subtype > max_patient_patches
            'VOA-2000': {
                'VOA-2000A': ['/Tumor/VOA-2000A/1', '/Tumor/VOA-2000A/2', '/Tumor/VOA-2000A/3'],
                'VOA-2000B': ['/Tumor/VOA-2000B/1', '/Tumor/VOA-2000B/2', '/Tumor/VOA-2000B/3'],
                'VOA-2000C': ['/Tumor/VOA-2000C/1', '/Tumor/VOA-2000C/2', '/Tumor/VOA-2000C/3'],
            },
            # Each subtype empty or < max_patient_patches
            # 'VOA-3000': { },
        },
        'Necrosis': {
            'VOA-1000': {
                'VOA-1000A': ['/Necrosis/VOA-1000A/1']
            },
            'VOA-2000': {
                'VOA-2000A': ['/Necrosis/VOA-2000A/1', '/Necrosis/VOA-2000A/2'],
                'VOA-2000B': ['/Necrosis/VOA-2000B/1', '/Necrosis/VOA-2000B/2', '/Necrosis/VOA-2000B/3'],
                'VOA-2000C': ['/Necrosis/VOA-2000C/1', '/Necrosis/VOA-2000C/2', '/Necrosis/VOA-2000C/3'],
            },
            'VOA-3000': {
                'VOA-3000A': ['/Necrosis/VOA-3000A/1']
            },
        },
        'Stroma': {
            'VOA-1000': {
                'VOA-1000A': ['/Stroma/VOA-1000A/1'],
            },
            'VOA-2000': {
                'VOA-2000A': ['/Stroma/VOA-2000A/1', '/Stroma/VOA-2000A/2'],
                'VOA-2000B': ['/Stroma/VOA-2000B/1', '/Stroma/VOA-2000B/2'],
                'VOA-2000C': ['/Stroma/VOA-2000C/1', '/Stroma/VOA-2000C/2', '/Stroma/VOA-2000C/3'],
            },
            'VOA-3000': {
                'VOA-3000A': ['/Stroma/VOA-3000A/1', '/Stroma/VOA-3000A/2']
            },
        },
    }
    patient_subtype_patch_to_select_count, patient_subtype_patch_count = gc.create_patient_subtype_patch_to_select_count(
            subtype_patient_slide_patch)
    assert patient_subtype_patch_to_select_count == {
            'VOA-1000': {'Tumor': 4, 'Necrosis': 1, 'Stroma': 1},
            'VOA-2000': {'Tumor': 2, 'Necrosis': 2, 'Stroma': 2},
            'VOA-3000': {'Necrosis': 1, 'Stroma': 2}}
    assert patient_subtype_patch_count == {
            'VOA-1000': {'Tumor': 7, 'Necrosis': 1, 'Stroma': 1},
            'VOA-2000': {'Tumor': 9, 'Necrosis': 8, 'Stroma': 7},
            'VOA-3000': {'Necrosis': 1, 'Stroma': 2}}

def test_create_patient_subtype_patch_to_select_count_2():
    args_str = f"""
    from-arguments
    --patch_location {MOCK_PATCH_DIR}
    --out_location {OUTPUT_DIR}
    --is_binary
    --max_patient_patches 6
    """
    parser = create_parser()
    config = parser.get_args(args_str.split())
    gc = GroupCreator(config)
    subtype_patient_slide_patch = {
        'Tumor': {
            # Balanced with each total > max_patient_patches but each subtype < max_patient_patches
            'VOA-1000': {
                'VOA-1000A': ['/Tumor/VOA-1000A/1', '/Tumor/VOA-1000A/2', '/Tumor/VOA-1000A/3'],
            },
            # Mainly Tumor with Tumor, Stroma > max_patient_patches
            'VOA-2000': {
                'VOA-2000A': ['/Tumor/VOA-2000A/1', '/Tumor/VOA-2000A/2', '/Tumor/VOA-2000A/3'],
                'VOA-2000B': ['/Tumor/VOA-2000B/1', '/Tumor/VOA-2000B/2', '/Tumor/VOA-2000B/3'],
                'VOA-2000C': ['/Tumor/VOA-2000C/1', '/Tumor/VOA-2000C/2', '/Tumor/VOA-2000C/3'],
            },
            # total == max_patient_patches
            'VOA-3000': {
                'VOA-3000A': ['/Tumor/VOA-3000A/1', '/Tumor/VOA-3000A/2'],
                'VOA-3000B': ['/Tumor/VOA-3000B/1',],
            },
        },
        'Necrosis': {
            'VOA-1000': {
                'VOA-2000A': ['/Tumor/VOA-2000A/1', '/Tumor/VOA-2000A/2'],
            },
            'VOA-2000': {
                'VOA-2000A': ['/Necrosis/VOA-2000A/1', '/Necrosis/VOA-2000A/2'],
            },
            'VOA-3000': {
                'VOA-3000A': ['/Necrosis/VOA-3000A/1']
            },
        },
        'Stroma': {
            'VOA-1000': {
                'VOA-1000A': ['/Stroma/VOA-1000A/1'],
                'VOA-1000B': ['/Stroma/VOA-1000B/1'],
                'VOA-1000C': ['/Stroma/VOA-1000C/1'],
            },
            'VOA-2000': {
                'VOA-2000A': ['/Stroma/VOA-2000A/1', '/Stroma/VOA-2000A/2'],
                'VOA-2000B': ['/Stroma/VOA-2000B/1', '/Stroma/VOA-2000B/2'],
                'VOA-2000C': ['/Stroma/VOA-2000C/1', '/Stroma/VOA-2000C/2', '/Stroma/VOA-2000C/3'],
            },
            'VOA-3000': {
                'VOA-3000A': ['/Stroma/VOA-3000A/1', '/Stroma/VOA-3000A/2']
            },
        },
    }
    patient_subtype_patch_to_select_count, patient_subtype_patch_count = gc.create_patient_subtype_patch_to_select_count(
            subtype_patient_slide_patch)
    assert patient_subtype_patch_to_select_count == {
            'VOA-1000': {'Tumor': 2, 'Necrosis': 2, 'Stroma': 2},
            'VOA-2000': {'Tumor': 2, 'Necrosis': 2, 'Stroma': 2},
            'VOA-3000': {'Tumor': 3, 'Necrosis': 1, 'Stroma': 2}}
    assert patient_subtype_patch_count == {
            'VOA-1000': {'Tumor': 3, 'Necrosis': 2, 'Stroma': 3},
            'VOA-2000': {'Tumor': 9, 'Necrosis': 2, 'Stroma': 7},
            'VOA-3000': {'Tumor': 3, 'Necrosis': 1, 'Stroma': 2}}

def test_create_patient_subtype_patch_to_select_count_3():
    args_str = f"""
    from-arguments
    --patch_location {MOCK_PATCH_DIR}
    --out_location {OUTPUT_DIR}
    --max_patient_patches 3
    """
    parser = create_parser()
    config = parser.get_args(args_str.split())
    gc = GroupCreator(config)
    subtype_patient_slide_patch = {
        'MMRD': {
            'VOA-1000': {
                'VOA-1000A': ['/MMRD/VOA-1000A/1', '/MMRD/VOA-1000A/2', '/MMRD/VOA-1000A/3', '/MMRD/VOA-1000A/4'],
            },
        },
        'POLE': {
            'VOA-2000': {
                'VOA-2000A': ['/POLE/VOA-2000A/1', '/POLE/VOA-2000A/2',],
            },
        },
    }
    patient_subtype_patch_to_select_count, patient_subtype_patch_count = gc.create_patient_subtype_patch_to_select_count(
            subtype_patient_slide_patch)
    assert patient_subtype_patch_to_select_count == {'VOA-1000': {'MMRD': 3}, 'VOA-2000': {'POLE': 2}}
    assert patient_subtype_patch_count == {'VOA-1000': {'MMRD': 4}, 'VOA-2000': {'POLE': 2}}
