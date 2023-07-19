# -*- coding: utf-8 -*-
"""
Created the 14/07/2023

@author: Sebastien Weber
"""

import pytest
from importlib import metadata

from pymodaq.utils.daq_utils import get_plugins

DET_TYPES = {'DAQ0D': get_plugins('daq_0Dviewer'),
             'DAQ1D': get_plugins('daq_1Dviewer'),
             'DAQ2D': get_plugins('daq_2Dviewer'),
             'DAQND': get_plugins('daq_NDviewer'),
             }


def test_mock_detectors():
    assert 'Mock' in [det['name'] for det in DET_TYPES['DAQ0D']]
    assert 'Mock' in [det['name'] for det in DET_TYPES['DAQ1D']]
    assert 'Mock' in [det['name'] for det in DET_TYPES['DAQ2D']]
    assert 'Mock' in [det['name'] for det in DET_TYPES['DAQND']]
