from pathlib import Path
from .utils import Config
from pymodaq_utils.config import GlobalConfig

config = GlobalConfig()


from pymodaq_utils.utils import get_version
__version__ = get_version(__package__)
