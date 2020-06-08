from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, QThread
from pymodaq.daq_utils import daq_utils as utils
import numpy as np
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base
from easydict import EasyDict as edict
from collections import OrderedDict
from pymodaq.daq_utils.daq_utils import gauss1D
from pymodaq.daq_viewer.utility_classes import comon_parameters
from pymodaq_plugins.daq_viewer_plugins.plugins_1D.daq_1Dviewer_Mock import DAQ_1DViewer_Mock
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

class DAQ_1DViewer_MockAdaptive(DAQ_1DViewer_Mock):
    """
        =============== =================
        **Attributes**  **Type**
        *params*        dictionnary list
        *x_axis*        1D numpy array
        *ind_data*      int
        =============== =================
    """

    def __init__(self, parent=None,
                 params_state=None):  # init_params is a list of tuple where each tuple contains info on a 1D channel (Ntps,amplitude, width, position and noise)
        super().__init__(parent, params_state)


    def grab_data(self, Naverage=1, **kwargs):
        """

        """
        if 'positions' in kwargs:
            positions = kwargs['positions']
            if len(positions) == 2:
                weight = random_hypergaussians_signal(positions)
            else:
                weight = random_1D(positions)
        else:
            weight = random_hypergaussians((xaxis, yaxis)).reshape(-1)[self.ind_data]

        Naverage = 1
        data_tot = self.set_Mock_data()
        for ind in range(Naverage - 1):
            data_tmp = self.set_Mock_data()
            QThread.msleep(100)

            for ind, data in enumerate(data_tmp):
                data_tot[ind] += data

        data_tot = [weight*data / Naverage for data in data_tot]

        self.data_grabed_signal.emit([utils.DataFromPlugins(name='MockAdaptive', data=data_tot, dim='Data1D')])
        self.ind_data += 1

