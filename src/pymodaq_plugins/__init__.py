from pathlib import Path

with open(str(Path(__file__).parent.joinpath('VERSION')), 'r') as fvers:
    __version__ = fvers.read().strip()
