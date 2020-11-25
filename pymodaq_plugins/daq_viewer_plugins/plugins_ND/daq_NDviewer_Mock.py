from PyQt5.QtCore import QThread
from PyQt5 import QtWidgets
import numpy as np
import pymodaq.daq_utils.daq_utils as utils
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base
from easydict import EasyDict as edict
from collections import OrderedDict
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo, Axis, DataFromPlugins, NavAxis
from pymodaq.daq_viewer.utility_classes import comon_parameters


class DAQ_NDViewer_Mock(DAQ_Viewer_base):
    """
        =============== ==================
        **Attributes**   **Type**
        *params*         dictionnary list
        *x_axis*         1D numpy array
        *y_axis*         1D numpy array
        =============== ==================

        See Also
        --------
        utility_classes.DAQ_Viewer_base
    """

    params = comon_parameters + [
        {'name': 'rolling', 'type': 'int', 'value': 1, 'min': 0},
        {'name': 'amp_noise', 'type': 'float', 'value': 4, 'default': 0.1, 'min': 0},
        {'title': 'Spatial properties:', 'name': 'spatial_settings', 'type': 'group', 'children': [
            {'title': 'Nx', 'name': 'Nx', 'type': 'int', 'value': 100, 'default': 100, 'min': 1},
            {'title': 'Ny', 'name': 'Ny', 'type': 'int', 'value': 200, 'default': 200, 'min': 1},
            {'title': 'amp', 'name': 'amp', 'type': 'int', 'value': 20, 'default': 20, 'min': 1},
            {'title': 'x0', 'name': 'x0', 'type': 'slide', 'value': 50, 'default': 50, 'min': 0},
            {'title': 'y0', 'name': 'y0', 'type': 'float', 'value': 100, 'default': 100, 'min': 0},
            {'title': 'dx', 'name': 'dx', 'type': 'float', 'value': 20, 'default': 20, 'min': 1},
            {'title': 'dy', 'name': 'dy', 'type': 'float', 'value': 40, 'default': 40, 'min': 1},
            {'title': 'lambda', 'name': 'lambda', 'type': 'float', 'value': 8, 'default': 1, 'min': 0.1},
            {'title': 'n', 'name': 'n', 'type': 'float', 'value': 1, 'default': 1, 'min': 1},
        ]},
        {'title': 'Temporal properties:', 'name': 'temp_settings', 'type': 'group', 'children': [
            {'title': 'Nt', 'name': 'Nt', 'type': 'int', 'value': 150, 'default': 100, 'min': 1},
            {'title': 'amp', 'name': 'amp', 'type': 'int', 'value': 20, 'default': 20, 'min': 1},
            {'title': 't0', 'name': 't0', 'type': 'slide', 'value': 50, 'default': 50, 'min': 0},
            {'title': 'dt', 'name': 'dt', 'type': 'float', 'value': 20, 'default': 20, 'min': 1},
            {'title': 'n', 'name': 'n', 'type': 'float', 'value': 1, 'default': 1, 'min': 1},
        ]},

        {'title': 'Cam. Prop.:', 'name': 'cam_settings', 'type': 'group', 'children': []},
    ]

    def __init__(self, parent=None,
                 params_state=None):  # init_params is a list of tuple where each tuple contains info on a 1D channel (Ntps,amplitude, width, position and noise)
        super().__init__(parent, params_state)
        self.x_axis = None
        self.y_axis = None
        self.live = False
        self.ind_commit = 0
        self.ind_data = 0

    def commit_settings(self, param):
        """
            Activate parameters changes on the hardware.

            =============== ================================ ===========================
            **Parameters**   **Type**                          **Description**
            *param*          instance of pyqtgraph Parameter   the parameter to activate
            =============== ================================ ===========================

            See Also
            --------
            set_Mock_data
        """
        self.set_Mock_data()

    def set_Mock_data(self):
        """
            | Set the x_axis and y_axis with a linspace distribution from settings parameters.
            |

            Once done, set the data mock with parameters :
                * **Amp** : The amplitude
                * **x0** : the origin of x
                * **dx** : the derivative x pos
                * **y0** : the origin of y
                * **dy** : the derivative y pos
                * **n** : ???
                * **amp_noise** : the noise amplitude

            Returns
            -------
                The computed data mock.
        """
        image = np.zeros((self.settings.child('spatial_settings', 'Ny').value(),
                          self.settings.child('spatial_settings', 'Nx').value(),
                          self.settings.child('temp_settings', 'Nt').value()))

        self.time_axis = np.linspace(0, self.settings.child('temp_settings', 'Nt').value(),
                                     self.settings.child('temp_settings', 'Nt').value(),
                                     endpoint=False)

        if self.settings.child('ROIselect', 'use_ROI').value():
            self.x_axis = np.linspace(self.settings.child('ROIselect', 'x0').value(),
                                      self.settings.child('ROIselect', 'x0').value() + self.settings.child('ROIselect',
                                                                                                           'width').value(),
                                      self.settings.child('ROIselect', 'width').value(), endpoint=False)
            self.y_axis = np.linspace(self.settings.child('ROIselect', 'y0').value(),
                                      self.settings.child('ROIselect', 'y0').value() + self.settings.child('ROIselect',
                                                                                                           'height').value(),
                                      self.settings.child('ROIselect', 'height').value(), endpoint=False)

            data_mock = self.settings.child('spatial_settings', 'amp').value() * (
                utils.gauss2D(self.x_axis, self.settings.child('spatial_settings', 'x0').value(),
                              self.settings.child('spatial_settings', 'dx').value(),
                              self.y_axis, self.settings.child('spatial_settings', 'y0').value(),
                              self.settings.child('spatial_settings', 'dy').value(),
                              self.settings.child('spatial_settings', 'n').value())) + self.settings.child(
                ('amp_noise')).value() * np.random.rand(len(self.y_axis), len(self.x_axis))

            for indy in range(data_mock.shape[0]):
                data_mock[indy, :] = data_mock[indy, :] * np.sin(
                    self.x_axis / self.settings.child('spatial_settings', 'lambda').value()) ** 2
            data_mock = np.roll(data_mock, self.ind_data * self.settings.child('rolling').value(), axis=1)

            try:
                self.image[
                    self.settings.child('ROIselect', 'y0').value():
                    self.settings.child('ROIselect', 'y0').value() + self.settings.child('ROIselect', 'height').value(),
                    self.settings.child('ROIselect', 'x0').value():
                    self.settings.child('ROIselect', 'x0').value() + self.settings.child('ROIselect', 'width').value()] \
                    = data_mock

            except Exception as e:
                self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))
        else:
            self.x_axis = np.linspace(0, self.settings.child('spatial_settings', 'Nx').value(),
                                      self.settings.child('spatial_settings', 'Nx').value(),
                                      endpoint=False)
            self.y_axis = np.linspace(0, self.settings.child('spatial_settings', 'Ny').value(),
                                      self.settings.child('spatial_settings', 'Ny').value(),
                                      endpoint=False)

            data_mock = self.settings.child('spatial_settings', 'amp').value() * (
                utils.gauss2D(self.x_axis, self.settings.child('spatial_settings', 'x0').value(),
                              self.settings.child('spatial_settings', 'dx').value(),
                              self.y_axis, self.settings.child('spatial_settings', 'y0').value(),
                              self.settings.child('spatial_settings', 'dy').value(),
                              self.settings.child('spatial_settings', 'n').value())) + \
                self.settings.child(('amp_noise')).value() * \
                np.random.rand(len(self.y_axis), len(self.x_axis))

            for indy in range(data_mock.shape[0]):
                data_mock[indy, :] = data_mock[indy, :] * np.sin(
                    self.x_axis / self.settings.child('spatial_settings', 'lambda').value()) ** 2

            ind = 0
            for indy in range(data_mock.shape[0]):
                for indx in range(data_mock.shape[1]):
                    image[indy, indx, :] = data_mock[indy, indx] * \
                        utils.gauss1D(self.time_axis, self.settings.child('temp_settings', 't0').value(),
                                      self.settings.child('temp_settings', 'dt').value(),
                                      self.settings.child('temp_settings', 'n').value()) * \
                        np.sin(np.roll(self.time_axis, ind) / 4) ** 2
                    ind += 1

            image = np.roll(image, self.ind_data * self.settings.child(('rolling')).value(), axis=1)

            self.image = image

        self.ind_data += 1

        QThread.msleep(100)

        return self.image

    def ini_detector(self, controller=None):
        """
            Initialisation procedure of the detector initializing the status dictionnary.

            See Also
            --------
            daq_utils.ThreadCommand, get_xaxis, get_yaxis
        """
        self.status.update(edict(initialized=False, info="", x_axis=None, y_axis=None, controller=None))
        try:

            if self.settings.child(('controller_status')).value() == "Slave":
                if controller is None:
                    raise Exception('no controller has been defined externally while this detector is a slave one')
                else:
                    self.controller = controller
            else:
                self.controller = "Mock controller"

            self.set_Mock_data()
            # initialize viewers with the future type of data
            self.data_grabed_signal_temp.emit(
                [DataFromPlugins(name='MockND', data=[np.zeros((128, 30, 10))], dim='DataND',
                                 nav_axes=(0, 1)), ])

            self.status.x_axis = self.x_axis
            self.status.y_axis = self.y_axis
            self.status.initialized = True
            self.status.controller = self.controller
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))
            self.status.info = getLineInfo() + str(e)
            self.status.initialized = False
            return self.status

    def close(self):
        """
            not implemented.
        """
        pass

    def grab_data(self, Naverage=1, **kwargs):
        """
            | For each integer step of naverage range set mock data.
            | Construct the data matrix and send the data_grabed_signal once done.

            =============== ======== ===============================================
            **Parameters**  **Type**  **Description**
            *Naverage*      int       The number of images to average.
                                      specify the threshold of the mean calculation
            =============== ======== ===============================================

            See Also
            --------
            set_Mock_data
        """

        "live is an attempt to export data as fast as possible"
        if 'live' in kwargs:
            if kwargs['live']:
                self.live = True
                self.live = False  # don't want to use that for the moment

        if self.live:
            while self.live:
                data = self.average_data(Naverage)
                QThread.msleep(100)
                self.data_grabed_signal.emit(data)
                QtWidgets.QApplication.processEvents()
        else:
            data = self.average_data(Naverage)
            QThread.msleep(000)
            self.data_grabed_signal.emit(data)

    def average_data(self, Naverage):
        data_tmp = np.zeros_like(self.image)
        for ind in range(Naverage):
            data_tmp += self.set_Mock_data()
        data_tmp = data_tmp / Naverage

        data = [DataFromPlugins(name='MockND_{:d}'.format(ind), data=[data_tmp], dim='DataND', nav_axes=(1, 0),
                                nav_x_axis=NavAxis(data=self.x_axis, label='X space', nav_index=1),
                                nav_y_axis=NavAxis(data=self.y_axis, label='Y space', nav_index=0),
                                x_axis=Axis(data=self.time_axis, label='time label'))]
        return data

    def stop(self):
        """
            not implemented.
        """
        self.live = False
        return ""
