from PyQt5.QtCore import QThread
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base
import numpy as np
from easydict import EasyDict as edict
from collections import OrderedDict
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo
from pymodaq.daq_utils.daq_utils import gauss1D
from pymodaq.daq_viewer.utility_classes import comon_parameters
from .daq_1Dviewer_Mock_spectro import DAQ_1DViewer_Mock_spectro


class DAQ_1DViewer_Mock(DAQ_1DViewer_Mock_spectro):
    """
    Derived class from DAQ_1DViewer_Mock_spectro
    Simulates a pixaleted spectrometer detector without builtin calibration of its energy axis
    """

    def __init__(self, parent=None,
                 params_state=None):  # init_params is a list of tuple where each tuple contains info on a 1D channel (Ntps,amplitude, width, position and noise)
        super().__init__(parent, params_state)

    def ini_detector(self, controller=None):
        """
            Initialisation procedure of the detector updating the status dictionnary.

            See Also
            --------
            set_Mock_data, daq_utils.ThreadCommand
        """

        self.settings.child('x_axis', 'Npts').setValue(512)
        self.settings.child('x_axis', 'x0').setValue(256)
        self.settings.child('x_axis', 'dx').setValue(1)
        super().ini_detector(controller)
        # self.set_x_axis()

        self.settings.child('Mock1', 'x0').setValue(125)
        self.settings.child('Mock1', 'dx').setValue(20)

        self.settings.child('Mock2', 'x0').setValue(325)
        self.settings.child('Mock2', 'dx').setValue(20)

        self.settings.child(('multi')).setValue(True)
        self.settings.child(('rolling')).setValue(1)

        self.settings.child(("laser_wl")).hide()
        self.settings.child(('exposure_ms')).hide()

        return self.status
