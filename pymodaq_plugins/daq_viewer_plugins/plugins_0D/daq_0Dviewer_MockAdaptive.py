from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, QThread
from pymodaq.daq_utils import daq_utils as utils
import numpy as np
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base
from easydict import EasyDict as edict
from collections import OrderedDict
from pymodaq.daq_utils.daq_utils import gauss1D
from pymodaq.daq_viewer.utility_classes import comon_parameters

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
amp = np.random.rand(Nstruct) * 100
xaxis = np.linspace(*xlim, Npts)
yaxis = np.linspace(*ylim, Npts)


def random_hypergaussians(xy):
    x, y = xy
    if not hasattr(x, '__len__'):
        x = [x]
    if not hasattr(y, '__len__'):
        y = [y]
    signal = np.zeros((len(x), len(y)))
    for ind in range(Nstruct):
        signal += amp[ind] * utils.gauss2D(x, x0s[ind], dx[ind], y, y0s[ind], dy[ind], 2)
    signal += 0.1*np.random.rand(len(x), len(y))
    return signal


def random_hypergaussians_signal(xy):
    return random_hypergaussians(xy)[0, 0]

def random_1D(xy):
    return 0.

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
    ]

    def __init__(self, parent=None,
                 params_state=None):  # init_params is a list of tuple where each tuple contains info on a 1D channel (Ntps,amplitude, width, position and noise)
        super().__init__(parent, params_state)
        self.x_axis = None
        self.ind_data = 0

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
        if 'positions' in kwargs:
            positions = kwargs['positions']
            if len(positions) == 2:
                data = random_hypergaussians_signal(positions)
            else:
                data = random_1D(positions)
        else:
            data = random_hypergaussians((xaxis, yaxis)).reshape(-1)[self.ind_data]

        self.data_grabed_signal.emit([utils.DataFromPlugins(name='MockAdaptive', data=[np.array([data])],
                                                            dim='Data0D', )])
        self.ind_data += 1

    def stop(self):
        """
            not implemented.
        """

        return ""
