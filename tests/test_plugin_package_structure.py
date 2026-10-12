"""Acceptance tests of the plugin, provided by PyMoDAQ (from version 5.3.2).

They check the package structure, the entry points, the naming of the instrument modules and classes, the mandatory
attributes and methods of the plugin classes, and apply the static rules of PyMoDAQ on the sources
(see https://pymodaq.cnrs.fr/en/latest/developer_folder/instrument_plugins.html#testing-your-plugin).

The unfinished parts of the plugin (TODO comments, placeholders) are listed but do not fail the tests, set
``fail_on = 'todo'`` before a release. Add your own tests, specific to your instruments, in other files.
"""
import importlib.util

import pytest

try:
    available = importlib.util.find_spec('pymodaq.utils.plugin_testing') is not None
except ModuleNotFoundError:  # pymodaq is not installed
    available = False
if not available:
    pytest.skip('The plugin acceptance checks need PyMoDAQ >= 5.3.2', allow_module_level=True)

from pymodaq.utils.plugin_testing import PluginPackageChecks


class TestPlugin(PluginPackageChecks):
    # package_name = 'pymodaq_plugins_xxxx'  # only if it cannot be found from the pyproject.toml and the package folder
    fail_on = 'error'  # 'error', 'warning' or 'todo' (also fail on the unfinished parts)
    strict_imports = False  # True: also fail when a module cannot be imported (missing dependency or driver); the
    # modules of an instrument whose driver cannot be installed on the CI runner are then skipped, not failed
