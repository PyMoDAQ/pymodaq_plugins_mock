# -*- coding: utf-8 -*-
"""
Created the 17/10/2023

@author: Sebastien Weber
"""
import pytest
from pathlib import Path
import importlib
import pkgutil


MANDATORY_MOVE_METHODS = ['ini_attributes', 'get_actuator_value', 'close', 'commit_settings',
                          'ini_stage', 'move_abs', 'move_home', 'move_rel', 'stop_motion']
MANDATORY_VIEWER_METHODS = ['ini_attributes', 'grab_data', 'close', 'commit_settings',
                          'ini_detector', ]


def get_package_name():
    here = Path(__file__).parent
    package_name = here.parent.stem
    return package_name


def get_move_plugins():
    pkg_name = get_package_name()
    move_mod = importlib.import_module(f'{pkg_name}.daq_move_plugins')

    plugin_list = [mod for mod in [mod[1] for mod in
                                   pkgutil.iter_modules([str(move_mod.path.parent)])]
                   if 'daq_move_' in mod]
    return plugin_list, move_mod


def get_viewer_plugins(dim='0D'):
    pkg_name = get_package_name()
    viewer_mod = importlib.import_module(f'{pkg_name}.daq_viewer_plugins.plugins_{dim}')

    plugin_list = [mod for mod in [mod[1] for mod in
                                   pkgutil.iter_modules([str(viewer_mod.path.parent)])]
                   if f'daq_{dim}viewer_' in mod]
    return plugin_list, viewer_mod


def test_package_name_ok():
    assert 'pymodaq_plugins_' in get_package_name()[0:16]


def test_imports():
    pkg_name = get_package_name()
    mod = importlib.import_module(pkg_name)
    assert hasattr(mod, 'config')
    assert hasattr(mod, '__version__')
    move_mod = importlib.import_module(f'{pkg_name}', 'daq_move_plugins')
    importlib.import_module(f'{pkg_name}', 'daq_viewer_plugins')
    importlib.import_module(f'{pkg_name}', 'extensions')
    importlib.import_module(f'{pkg_name}', 'models')
    importlib.import_module(f'{pkg_name}.daq_viewer_plugins', 'plugins_0D')
    importlib.import_module(f'{pkg_name}.daq_viewer_plugins', 'plugins_1D')
    importlib.import_module(f'{pkg_name}.daq_viewer_plugins', 'plugins_2D')
    importlib.import_module(f'{pkg_name}.daq_viewer_plugins', 'plugins_ND')


def test_move_inst_plugins_name():
    plugin_list, move_mod = get_move_plugins()
    for plug in plugin_list:
        name = plug.split('daq_move_')[1]
        assert hasattr(getattr(move_mod, plug), f'DAQ_Move_{name}')


def test_move_has_mandatory_methods():
    plugin_list, move_mod = get_move_plugins()
    for plug in plugin_list:
        name = plug.split('daq_move_')[1]
        klass = getattr(getattr(move_mod, plug), f'DAQ_Move_{name}')
        for meth in MANDATORY_MOVE_METHODS:
            assert hasattr(klass, meth)


@pytest.mark.parametrize('dim', ('0D', '1D', '2D', 'ND'))
def test_viewer_has_mandatory_methods(dim):
    plugin_list, mod = get_viewer_plugins(dim)
    for plug in plugin_list:
        name = plug.split(f'daq_{dim}viewer_')[1]
        try:
            module = importlib.import_module(f'.{plug}', mod.__package__)
        except Exception:
            break
        klass = getattr(module, f'DAQ_{dim}Viewer_{name}')
        for meth in MANDATORY_VIEWER_METHODS:
            assert hasattr(klass, meth)
