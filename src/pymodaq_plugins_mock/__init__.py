from pathlib import Path
from .utils import Config

config = Config()


with open(str(Path(__file__).parent.joinpath('resources/VERSION')), 'r') as fvers:
    __version__ = fvers.read().strip()
