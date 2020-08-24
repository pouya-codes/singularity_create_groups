import shutil
import os
import os.path
import pytest

from create_groups.tests import (OUTPUT_DIR)

CLEAN_AFTER_RUN=False

@pytest.fixture
def clean_output():
    """Get the directory to save test outputs. Cleans the output directory before and after each test.
    """
    for file in os.listdir(OUTPUT_DIR):
        os.unlink(os.path.join(OUTPUT_DIR, file))
    yield None
    if CLEAN_AFTER_RUN:
        for file in os.listdir(OUTPUT_DIR):
            os.unlink(os.path.join(OUTPUT_DIR, file))
