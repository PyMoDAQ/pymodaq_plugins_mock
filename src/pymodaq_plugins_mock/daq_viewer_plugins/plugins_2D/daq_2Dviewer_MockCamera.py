from qtpy.QtCore import QThread, Slot, QRectF
from qtpy import QtWidgets
import numpy as np
import pymodaq.daq_utils.math_utils as mylib
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, main, comon_parameters
from easydict import EasyDict as edict
from collections import OrderedDict
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo, DataFromPlugins, Axis
from pymodaq.daq_utils.parameter import Parameter
from pymodaq.daq_utils.parameter.utils import iter_children
from pymodaq.daq_utils.array_manipulation import crop_array_to_axis, crop_vector_to_axis

from pymodaq_plugins_mock.hardware.camera_wrapper import Camera

class DAQ_2DViewer_MockCamera(DAQ_Viewer_base):

    params = comon_parameters + [
        {'title': 'Wait time (ms)', 'name': 'wait_time', 'type': 'int', 'value': 100, 'default': 100, 'min': 0},
        {'title': 'Nimages colors:', 'name': 'Nimagescolor', 'type': 'int', 'value': 1, 'default': 1, 'min': 0,
         'max': 3},
        {'title': 'Nimages pannels:', 'name': 'Nimagespannel', 'type': 'int', 'value': 1, 'default': 0, 'min': 0},
        {'title': 'Use ROISelect', 'name': 'use_roi_select', 'type': 'bool', 'value': False},
        {'title': 'Threshold', 'name': 'threshold', 'type': 'int', 'value': 1, 'min': 0},

        {'title': 'Values', 'name': 'current_values', 'type': 'group', 'children': [
            {'title': 'X', 'name': 'X', 'type': 'float', 'value': 0.},
            {'title': 'Y', 'name': 'Y', 'type': 'float', 'value': 0.},
            {'title': 'Theta', 'name': 'Theta', 'type': 'float', 'value': 0.},
        ]},
        {'title': 'Cam. Prop.:', 'name': 'cam_settings', 'type': 'group', 'children': [
            {'title': 'Fringes?', 'name': 'fringes', 'type': 'bool', 'value': True},
            {'title': 'Nx', 'name': 'Nx', 'type': 'int', 'value': Camera.Nx, 'min': 1},
            {'title': 'Ny', 'name': 'Ny', 'type': 'int', 'value': Camera.Ny, 'min': 1},
            {'title': 'Amp', 'name': 'amp', 'type': 'int', 'value': Camera.amp, 'min': 1},
            {'title': 'x0', 'name': 'x0', 'type': 'slide', 'value': Camera.x0, 'min': 0, 'max': 256},
            {'title': 'y0', 'name': 'y0', 'type': 'float', 'value': Camera.y0, 'min': 0},
            {'title': 'dx', 'name': 'dx', 'type': 'float', 'value': Camera.dx, 'min': 1},
            {'title': 'dy', 'name': 'dy', 'type': 'float', 'value': Camera.dy, 'min': 1},
            {'title': 'n', 'name': 'n', 'type': 'int', 'value': Camera.n, 'min': 1},
            {'title': 'amp_noise', 'name': 'amp_noise', 'type': 'float', 'value': Camera.amp_noise, 'min': 0},
        ]},

    ]

    def ini_attributes(self):
        self.controller: Camera = None

        self.x_axis = None
        self.y_axis = None
        self.live = False
        self.ind_commit = 0

    def commit_settings(self, param: Parameter):
        """
        """
        if param.name() in iter_children(self.settings.child('current_values'), []):
            self.controller.set_value(axis=param.name(), value=param.value())

        if param.name() in iter_children(self.settings.child('cam_settings'), []):
            if hasattr(self.controller, param.name()):
                setattr(self.controller, param.name(), param.value())
            self.controller.base_Mock_data()
            self.x_axis = Axis(data=self.controller.x_axis)
            self.y_axis = Axis(data=self.controller.y_axis)

    def ini_detector(self, controller=None):
        self.ini_detector_init(controller, Camera())
        self.emit_status(ThreadCommand('update_main_settings',
                                       [['wait_time'], self.settings['wait_time'], 'value']))

        self.controller.base_Mock_data()
        self.x_axis = Axis(data=self.controller.x_axis)
        self.y_axis = Axis(data=self.controller.y_axis)

        #apply presets to wrapper
        for settings in self.settings.child('cam_settings').children():
            if hasattr(self.controller, settings.name()):
                setattr(self.controller, settings.name(), settings.value())

        # initialize viewers with the future type of data but with 0value data
        self.data_grabed_signal_temp.emit(self.average_data(1, True),)

        initialized = True
        info = 'Controller ok'
        return info, initialized

    def close(self):
        pass

    def get_xaxis(self):
        """
        Get the current x_axis from the Mock data setting.

        Returns
        -------
        1D numpy array
            the current x_axis.

        See Also
        --------
        set_Mock_data
        """
        return self.controller.x_axis

    def get_yaxis(self):
        """
            Get the current y_axis from the Mock data setting.

            Returns
            -------
            1D numpy array
                the current y_axis.

            See Also
            --------
            set_Mock_data
        """
        return self.controller.y_axis

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

    def average_data(self, Naverage, init=False):
        data = []  # list of image (at most 3 for red, green and blue channels)
        data_tmp = np.zeros_like(self.controller.get_data())
        for ind in range(Naverage):
            data_tmp += self.controller.get_data()
        data_tmp = data_tmp / Naverage

        data_tmp = data_tmp * (data_tmp >= self.settings['threshold']) * (init is False)
        for ind in range(self.settings['Nimagespannel']):
            datatmptmp = []
            for indbis in range(self.settings['Nimagescolor']):
                datatmptmp.append(data_tmp)
            data.append(DataFromPlugins(name='Mock2D_{:d}'.format(ind), data=datatmptmp, dim='Data2D',
                                        x_axis=self.x_axis,
                                        y_axis=self.y_axis))
        # data.append(OrderedDict(name='Mock2D_1D',data=[np.mean(data_tmp,axis=0)], type='Data1D'))
        return data

    def stop(self):
        """
            not implemented.
        """
        self.live = False
        return ""


if __name__ == '__main__':
    main(__file__)
