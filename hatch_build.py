from pathlib import Path

from pymodaq_utils.resources.hatch_build_plugins import PluginInfoTomlHook

here = Path(__file__).absolute().parent


class PluginInfoTomlHook(PluginInfoTomlHook):
    def update(self, metadata: dict) -> None:
        super().update_custom(metadata, here)
