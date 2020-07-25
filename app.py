import create_groups.parser as parser
from create_groups import *

if __name__ == "__main__":
    config = parser.get_args()
    gc = GroupCreator(config)
    gc.run()
