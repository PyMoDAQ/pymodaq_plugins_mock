from pathlib import Path
from hatchling.metadata.plugin.interface import MetadataHookInterface
from pymodaq_utils.resources.hatch_build_plugins import update_metadata_from_toml

here = Path(__file__).absolute().parent


class PluginInfoTomlHook(MetadataHookInterface):
    def update(self, metadata: dict) -> None:
        update_metadata_from_toml(metadata, here)
