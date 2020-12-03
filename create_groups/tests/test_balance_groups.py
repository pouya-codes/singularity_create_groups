import pytest
import unittest
import random

import submodule_utils as utils
from create_groups.tests import (OUTPUT_DIR, MOCK_PATCH_DIR)
from create_groups.parser import create_parser
from create_groups import *
random.seed(default_seed)

def test_balance_groups_1():
    """
    Mock data distribution:
    || Patch Counts    || A || B || C || Total ||
    |  Patch in Group 1 | 5  | 4  | 3  | 12 |
    |  Patch in Group 2 | 10 | 9  | 11 | 30 |
    |  Patch in Group 3 | 6  | 7  | 8  | 21 |
    | Total             | 21 | 20 | 22 | 63 |
    """
    patch_pattern = 'subtype/slide'
    args_str = f"""
    from-arguments
    --patch_location {MOCK_PATCH_DIR}
    --out_location {OUTPUT_DIR}
    --patch_pattern {patch_pattern}
    --subtypes A=0 B=1 C=2
    """
    parser = create_parser()
    config = parser.get_args(args_str.split())
    gc = GroupCreator(config)
    assert {c.name: c.value for c in gc.CategoryEnum} == {'A': 0, 'B': 1, 'C': 2}

    groups_subtypes = {
        'group_1': {
            'A': [f"/A/V-1000/{i}" for i in range(5)],
            'B': [f"/B/V-1000/{i}" for i in range(4)],
            'C': [f"/C/V-1000/{i}" for i in range(3)],
        },
        'group_2': {
            'A': [f"/A/V-2000/{i}" for i in range(10)],
            'B': [f"/B/V-2000/{i}" for i in range(9)],
            'C': [f"/C/V-2000/{i}" for i in range(11)],
        },
        'group_3': {
            'A': [f"/A/V-3000/{i}" for i in range(6)],
            'B': [f"/B/V-3000/{i}" for i in range(7)],
            'C': [f"/C/V-3000/{i}" for i in range(8)],
        }
    }

    groups = gc.make_groups_from_groups_subtypes(groups_subtypes)
    assert len(groups) == 3
    assert utils.count(lambda p: 'A' in p, groups['group_1']) == 5
    assert utils.count(lambda p: 'B' in p, groups['group_1']) == 4
    assert utils.count(lambda p: 'C' in p, groups['group_1']) == 3
    assert len(groups['group_1']) == 12
    assert utils.count(lambda p: 'V-1000' in p, groups['group_1']) == 12
    assert utils.count(lambda p: 'A' in p, groups['group_2']) == 10
    assert utils.count(lambda p: 'B' in p, groups['group_2']) == 9
    assert utils.count(lambda p: 'C' in p, groups['group_2']) == 11
    assert len(groups['group_2']) == 30
    assert utils.count(lambda p: 'V-2000' in p, groups['group_2']) == 30
    assert utils.count(lambda p: 'A' in p, groups['group_3']) == 6
    assert utils.count(lambda p: 'B' in p, groups['group_3']) == 7
    assert utils.count(lambda p: 'C' in p, groups['group_3']) == 8
    assert len(groups['group_3']) == 21
    assert utils.count(lambda p: 'V-3000' in p, groups['group_3']) == 21

    gc.balance_patches = 'overall'
    groups = gc.make_groups_from_groups_subtypes(groups_subtypes)
    assert utils.count(lambda p: 'A' in p, groups['group_1']) == 3
    assert utils.count(lambda p: 'B' in p, groups['group_1']) == 3
    assert utils.count(lambda p: 'C' in p, groups['group_1']) == 3
    assert len(groups['group_1']) == 9
    assert utils.count(lambda p: 'V-1000' in p, groups['group_1']) == 9
    assert utils.count(lambda p: 'A' in p, groups['group_2']) == 3
    assert utils.count(lambda p: 'B' in p, groups['group_2']) == 3
    assert utils.count(lambda p: 'C' in p, groups['group_2']) == 3
    assert len(groups['group_2']) == 9
    assert utils.count(lambda p: 'V-2000' in p, groups['group_2']) == 9
    assert utils.count(lambda p: 'A' in p, groups['group_3']) == 3
    assert utils.count(lambda p: 'B' in p, groups['group_3']) == 3
    assert utils.count(lambda p: 'C' in p, groups['group_3']) == 3
    assert len(groups['group_3']) == 9
    assert utils.count(lambda p: 'V-3000' in p, groups['group_3']) == 9
    
    gc.balance_patches = 'group'
    groups = gc.make_groups_from_groups_subtypes(groups_subtypes)
    assert utils.count(lambda p: 'A' in p, groups['group_1']) == 3
    assert utils.count(lambda p: 'B' in p, groups['group_1']) == 3
    assert utils.count(lambda p: 'C' in p, groups['group_1']) == 3
    assert len(groups['group_1']) == 9
    assert utils.count(lambda p: 'V-1000' in p, groups['group_1']) == 9
    assert utils.count(lambda p: 'A' in p, groups['group_2']) == 9
    assert utils.count(lambda p: 'B' in p, groups['group_2']) == 9
    assert utils.count(lambda p: 'C' in p, groups['group_2']) == 9
    assert len(groups['group_2']) == 27
    assert utils.count(lambda p: 'V-2000' in p, groups['group_2']) == 27
    assert utils.count(lambda p: 'A' in p, groups['group_3']) == 6
    assert utils.count(lambda p: 'B' in p, groups['group_3']) == 6
    assert utils.count(lambda p: 'C' in p, groups['group_3']) == 6
    assert len(groups['group_3']) == 18
    assert utils.count(lambda p: 'V-3000' in p, groups['group_3']) == 18

    gc.balance_patches = 'category'
    groups = gc.make_groups_from_groups_subtypes(groups_subtypes)
    assert utils.count(lambda p: 'A' in p, groups['group_1']) == 5
    assert utils.count(lambda p: 'B' in p, groups['group_1']) == 4
    assert utils.count(lambda p: 'C' in p, groups['group_1']) == 3
    assert len(groups['group_1']) == 12
    assert utils.count(lambda p: 'V-1000' in p, groups['group_1']) == 12
    assert utils.count(lambda p: 'A' in p, groups['group_2']) == 5
    assert utils.count(lambda p: 'B' in p, groups['group_2']) == 4
    assert utils.count(lambda p: 'C' in p, groups['group_2']) == 3
    assert len(groups['group_2']) == 12
    assert utils.count(lambda p: 'V-2000' in p, groups['group_2']) == 12
    assert utils.count(lambda p: 'A' in p, groups['group_3']) == 5
    assert utils.count(lambda p: 'B' in p, groups['group_3']) == 4
    assert utils.count(lambda p: 'C' in p, groups['group_3']) == 3
    assert len(groups['group_3']) == 12
    assert utils.count(lambda p: 'V-3000' in p, groups['group_3']) == 12

    gc.balance_patches = ('overall', 7,)
    groups = gc.make_groups_from_groups_subtypes(groups_subtypes)
    assert utils.count(lambda p: 'A' in p, groups['group_1']) == 5
    assert utils.count(lambda p: 'B' in p, groups['group_1']) == 4
    assert utils.count(lambda p: 'C' in p, groups['group_1']) == 3
    assert len(groups['group_1']) == 12
    assert utils.count(lambda p: 'V-1000' in p, groups['group_1']) == 12
    assert utils.count(lambda p: 'A' in p, groups['group_2']) == 7
    assert utils.count(lambda p: 'B' in p, groups['group_2']) == 7
    assert utils.count(lambda p: 'C' in p, groups['group_2']) == 7
    assert len(groups['group_2']) == 21
    assert utils.count(lambda p: 'V-2000' in p, groups['group_2']) == 21
    assert utils.count(lambda p: 'A' in p, groups['group_3']) == 6
    assert utils.count(lambda p: 'B' in p, groups['group_3']) == 7
    assert utils.count(lambda p: 'C' in p, groups['group_3']) == 7
    assert len(groups['group_3']) == 20
    assert utils.count(lambda p: 'V-3000' in p, groups['group_3']) == 20

    gc.balance_patches = ('group', 21,)
    groups = gc.make_groups_from_groups_subtypes(groups_subtypes)
    assert utils.count(lambda p: 'A' in p, groups['group_1']) == 5
    assert utils.count(lambda p: 'B' in p, groups['group_1']) == 4
    assert utils.count(lambda p: 'C' in p, groups['group_1']) == 3
    assert len(groups['group_1']) == 12
    assert utils.count(lambda p: 'V-1000' in p, groups['group_1']) == 12
    assert utils.count(lambda p: 'A' in p, groups['group_2']) == 7
    assert utils.count(lambda p: 'B' in p, groups['group_2']) == 7
    assert utils.count(lambda p: 'C' in p, groups['group_2']) == 7
    assert len(groups['group_2']) == 21
    assert utils.count(lambda p: 'V-2000' in p, groups['group_2']) == 21
    assert utils.count(lambda p: 'A' in p, groups['group_3']) == 6
    assert utils.count(lambda p: 'B' in p, groups['group_3']) == 7
    assert utils.count(lambda p: 'C' in p, groups['group_3']) == 8
    assert len(groups['group_3']) == 21
    assert utils.count(lambda p: 'V-3000' in p, groups['group_3']) == 21


def test_balance_groups_2():
    """
    Mock data distribution:
    || Patch Counts || A || B || C || Total ||
    |  Patch in Group 1 | 5 | 11 | 6 | 22 |
    |  Patch in Group 2 | 3 | 10 | 7 | 20 |
    |  Patch in Group 3 | 4 | 9 | 8 | 21 |
    | Total | 12 | 30 | 21 | 63 |
    """
    patch_pattern = 'subtype/slide'
    args_str = f"""
    from-arguments
    --patch_location {MOCK_PATCH_DIR}
    --out_location {OUTPUT_DIR}
    --patch_pattern {patch_pattern}
    --balance_patches category=21
    --subtypes A=0 B=1 C=2
    """
    parser = create_parser()
    config = parser.get_args(args_str.split())
    gc = GroupCreator(config)
    assert {c.name: c.value for c in gc.CategoryEnum} == {'A': 0, 'B': 1, 'C': 2}
    assert gc.balance_patches == ('category', 21,)
    groups_subtypes = {
        'group_1': {
            'A': [f"/A/V-1000/{i}" for i in range(5)],
            'B': [f"/B/V-1000/{i}" for i in range(11)],
            'C': [f"/C/V-1000/{i}" for i in range(6)],
        },
        'group_2': {
            'A': [f"/A/V-2000/{i}" for i in range(3)],
            'B': [f"/B/V-2000/{i}" for i in range(10)],
            'C': [f"/C/V-2000/{i}" for i in range(7)],
        },
        'group_3': {
            'A': [f"/A/V-3000/{i}" for i in range(4)],
            'B': [f"/B/V-3000/{i}" for i in range(9)],
            'C': [f"/C/V-3000/{i}" for i in range(8)],
        }
    }
    groups = gc.make_groups_from_groups_subtypes(groups_subtypes)
    assert utils.count(lambda p: 'A' in p, groups['group_1']) == 5
    assert utils.count(lambda p: 'B' in p, groups['group_1']) == 7
    assert utils.count(lambda p: 'C' in p, groups['group_1']) == 6
    assert len(groups['group_1']) == 18
    assert utils.count(lambda p: 'V-1000' in p, groups['group_1']) == 18
    assert utils.count(lambda p: 'A' in p, groups['group_2']) == 3
    assert utils.count(lambda p: 'B' in p, groups['group_2']) == 7
    assert utils.count(lambda p: 'C' in p, groups['group_2']) == 7
    assert len(groups['group_2']) == 17
    assert utils.count(lambda p: 'V-2000' in p, groups['group_2']) == 17
    assert utils.count(lambda p: 'A' in p, groups['group_3']) == 4
    assert utils.count(lambda p: 'B' in p, groups['group_3']) == 7
    assert utils.count(lambda p: 'C' in p, groups['group_3']) == 8
    assert len(groups['group_3']) == 19
    assert utils.count(lambda p: 'V-3000' in p, groups['group_3']) == 19