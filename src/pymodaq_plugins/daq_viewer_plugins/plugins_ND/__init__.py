import importlib
from pathlib import Path
from pymodaq.daq_utils import daq_utils as utils
logger = utils.set_logger('viewerND_plugins', add_to_console=False)

for path in Path(__file__).parent.iterdir():
    try:
        if '__init__' not in str(path):
            importlib.import_module('.' + path.stem, __package__)
    except Exception as e:
        logger.warning(f"{path.stem} plugin couldn't be loaded due to some missing packages or errors: {str(e)}")
