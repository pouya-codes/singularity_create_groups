import logging

from submodule_utils.logging import logger_factory
from create_groups.parser import create_parser
from create_groups import *

logger_factory()
logger = logging.getLogger('create_groups')

if __name__ == "__main__":
    parser = create_parser()
    config = parser.get_args()
    gc = GroupCreator(config)
    gc.run()
