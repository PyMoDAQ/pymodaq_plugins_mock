from qtpy.QtCore import QThread, Slot, QRectF
from qtpy import QtWidgets
import numpy as np
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, main, comon_parameters

from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq.utils.parameter import Parameter
from pymodaq.utils.parameter.utils import iter_children


from pymodaq_plugins_mock.hardware.camera_wrapper import Camera


class DAQ_2DViewer_MockCamera(DAQ_Viewer_base):

    live_mode_available = True
    hardware_averaging = True

    params = comon_parameters + [
        {'title': 'Wait time (ms)', 'name': 'wait_time', 'type': 'int', 'value': 100, 'default': 100, 'min': 0},
        {'title': 'Nimages colors:', 'name': 'Nimagescolor', 'type': 'int', 'value': 1, 'default': 1, 'min': 0,
         'max': 3},
        {'title': 'Nimages pannels:', 'name': 'Nimagespannel', 'type': 'int', 'value': 1, 'default': 0, 'min': 0},

        {'title': 'Read only prop:', 'name': 'read_only', 'type': 'bool', 'value': False},

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
        self._update_axes = True

    def commit_settings(self, param: Parameter):
        """
        """
        if param.name() in iter_children(self.settings.child('current_values'), []):
            self.controller.set_value(axis=param.name(), value=param.value())

        if param.name() in iter_children(self.settings.child('cam_settings'), []):
            if hasattr(self.controller, param.name()):
                setattr(self.controller, param.name(), param.value())
            self.controller.base_Mock_data()
            self.x_axis = Axis(data=self.controller.x_axis, label='pixel', index=1)
            self.y_axis = Axis(data=self.controller.y_axis, label='pixel', index=0)

        if param.name() == 'read_only':
            for child in self.settings.child('cam_settings').children():
                child.setOpts(readonly=param.value())

    def ini_detector(self, controller=None):
        self.ini_detector_init(controller, Camera())
        self.emit_status(ThreadCommand('update_main_settings',
                                       [['wait_time'], self.settings['wait_time'], 'value']))

        self.controller.base_Mock_data()
        self.x_axis = Axis(data=self.controller.x_axis, label='pixel', index=1)
        self.y_axis = Axis(data=self.controller.y_axis, label='pixel', index=0)

        #apply presets to wrapper
        for settings in self.settings.child('cam_settings').children():
            if hasattr(self.controller, settings.name()):
                setattr(self.controller, settings.name(), settings.value())

        # initialize viewers with the future type of data but with 0value data
        self.dte_signal_temp.emit(self.average_data(1, True),)

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
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging should be set to
            True in class preamble and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """
        if 'live' in kwargs:
            if kwargs['live']:
                self.live = True
                # self.live = False  # don't want to use that for the moment

        if self.live:
            while self.live:
                data = self.average_data(Naverage)  # hardware averaging
                QThread.msleep(kwargs.get('wait_time', 100))
                self.dte_signal.emit(data)
                QtWidgets.QApplication.processEvents()
        else:
            data = self.average_data(Naverage)  # hardware averaging
            QThread.msleep(000)
            self.dte_signal.emit(data)

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
            if self._update_axes:
                data.append(DataFromPlugins(name='Mock2D_{:d}'.format(ind), data=datatmptmp, dim='Data2D',
                                            axes=[self.x_axis, self.y_axis]))
            else:
                data.append(DataFromPlugins(name='Mock2D_{:d}'.format(ind), data=datatmptmp, dim='Data2D'))
        if self._update_axes:
            self._update_axes = False
        return DataToExport('MockCamera', data=data)

    def stop(self):
        """
            not implemented.
        """
        self.live = False
        return ""


if __name__ == '__main__':
    main(__file__)
