from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, QThread, pyqtSlot
from pymodaq.daq_utils import daq_utils as utils
import numpy as np
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base
from easydict import EasyDict as edict
from collections import OrderedDict
from pymodaq.daq_utils.daq_utils import gauss1D
from pymodaq.daq_viewer.utility_classes import comon_parameters
from pymodaq.daq_utils.scanner import ScanParameters

Nstruct = 10
xlim = [-5, 5]
ylim = [-5, 5]
dxmax = np.abs((np.max(xlim) - np.min(xlim)))
dymax = np.abs((np.max(ylim) - np.min(ylim)))

Npts = 1000
x0s = np.random.rand(Nstruct) * dxmax - np.max(xlim)
y0s = np.random.rand(Nstruct) * dymax - np.max(ylim)
dx = np.random.rand(Nstruct)
dy = np.random.rand(Nstruct)
amp = np.random.rand(Nstruct) * 10
slope = np.random.rand(Nstruct) / 10
xaxis = np.linspace(*xlim, Npts)
yaxis = np.linspace(*ylim, Npts)
x_axis1D = np.linspace(-5, 5, 501)


def random_hypergaussians2D(xy, coeff=1):
    x, y = xy
    if not hasattr(x, '__len__'):
        x = [x]
    if not hasattr(y, '__len__'):
        y = [y]
    signal = np.zeros((len(x), len(y)))
    for ind in range(Nstruct):
        signal += amp[ind] * utils.gauss2D(x, x0s[ind], coeff * dx[ind], y, y0s[ind], coeff * dy[ind], 2)
    signal += 0.1 * np.random.rand(len(x), len(y))
    return signal


def random_hypergaussians2D_signal(xy, coeff=1.0):
    return random_hypergaussians2D(xy, coeff)[0, 0]


def random_hypergaussians1D(x, coeff=1):
    signal = 0.
    for ind in range(Nstruct):
        signal += amp[ind] * utils.gauss1D(x, x0s[ind], coeff * dx[ind], 2)
    return signal


def diverging2D(xy, coeff=1.0):
    x, y = xy
    if not hasattr(x, '__len__'):
        x = [x]
    if not hasattr(y, '__len__'):
        y = [y]
    signal = np.zeros((len(x), len(y)))
    for ind in range(Nstruct):
        signal += amp[ind] * (coeff * slope[ind]) ** 2 / (
            (coeff * slope[ind]) ** 2 + (np.sqrt((x - x0s[ind]) ** 2 + (y - y0s[ind]) ** 2) ** 2))
        signal += 0.1 * np.random.rand(len(x), len(y))
    return signal


def diverging2D_signal(xy, coeff=1.0):
    return diverging2D(xy, coeff)[0, 0]


def diverging1D(x, coeff=1.0):
    signal = 0
    for ind in range(Nstruct):
        signal += amp[ind] * (coeff * slope[ind]) ** 2 / ((coeff * slope[ind]) ** 2 + (x - x0s[ind]) ** 2)
    return signal


class DAQ_0DViewer_MockAdaptive(DAQ_Viewer_base):
    """
        =============== =================
        **Attributes**  **Type**
        *params*        dictionnary list
        *x_axis*        1D numpy array
        *ind_data*      int
        =============== =================
    """
    params = comon_parameters + [
        {'title': 'Wait time (ms)', 'name': 'wait_time', 'type': 'int', 'value': 100, 'default': 100, 'min': 0},
        {'title': 'Show Scanner:', 'name': 'show_scanner', 'type': 'bool_push', 'value': False, },
        {'title': 'Function type:', 'name': 'fun_type', 'type': 'list', 'values': ['Gaussians', 'Lorentzians'], },
        {'title': 'Width coefficient', 'name': 'width_coeff', 'type': 'float', 'value': 1., 'min': 0},
    ]

    def __init__(self, parent=None,
                 params_state=None):  # init_params is a list of tuple where each tuple contains info on a 1D channel (Ntps,amplitude, width, position and noise)
        super().__init__(parent, params_state)
        self.x_axis = None
        self.ind_data = 0
        self.ind_grab = 0
        self.scan_parameters = None

    def commit_settings(self, param):
        """
            Setting the mock data.

            ============== ========= =================
            **Parameters**  **Type**  **Description**
            *param*         none      not used
            ============== ========= =================

            See Also
            --------
            set_Mock_data
        """
        if param.name() == 'wait_time':
            self.emit_status(utils.ThreadCommand('update_main_settings', [['wait_time'], param.value(), 'value']))

    def ini_detector(self, controller=None):
        """
            Initialisation procedure of the detector.

            Returns
            -------
            ???
                the initialized status.

            See Also
            --------
            set_Mock_data
        """

        self.status.update(edict(initialized=False, info="", x_axis=None, y_axis=None, controller=None))
        if self.settings.child(('controller_status')).value() == "Slave":
            if controller is None:
                raise Exception('no controller has been defined externally while this detector is a slave one')
            else:
                self.controller = controller
        else:
            self.controller = "Mock controller"
        self.emit_status(utils.ThreadCommand('update_main_settings', [['wait_time'],
                                                                      self.settings.child(('wait_time')).value(),
                                                                      'value']))

        # initialize viewers with the future type of data
        self.data_grabed_signal.emit(
            [utils.DataFromPlugins(name='Mock1', data=[np.array(0)], dim='Data0D', labels=['RandomGaussians'])])

        self.status.initialized = True
        self.status.controller = self.controller
        return self.status

    def close(self):
        """
            not implemented.
        """
        pass

    def grab_data(self, Naverage=1, **kwargs):
        """

        """
        coeff = self.settings.child(('width_coeff')).value()
        fun_type = self.settings.child(('fun_type')).value()
        if 'positions' in kwargs:
            positions = kwargs['positions']

            if len(positions) == 2:
                if fun_type == 'Gaussians':
                    data = random_hypergaussians2D_signal(positions, coeff)
                else:
                    data = diverging2D_signal(positions, coeff)
            else:
                if fun_type == 'Gaussians':
                    data = random_hypergaussians1D(positions, coeff)[0]
                else:
                    data = diverging1D(positions[0], coeff)
        else:
            if fun_type == 'Gaussians':
                data = random_hypergaussians1D(np.roll(x_axis1D, -self.ind_data)[0], coeff)
            else:
                data = diverging1D(np.roll(x_axis1D, -self.ind_data)[0], coeff)

        self.data_grabed_signal.emit([utils.DataFromPlugins(name='MockAdaptive', data=[np.array([data])],
                                                            dim='Data0D', )])
        self.ind_data += 1

    def stop(self):
        """
            not implemented.
        """

        return ""
