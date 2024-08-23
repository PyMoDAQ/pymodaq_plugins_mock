from pathlib import Path
from .utils import Config

config = Config()


from pymodaq_utils.utils import get_version
__version__ = get_version(__package__)
