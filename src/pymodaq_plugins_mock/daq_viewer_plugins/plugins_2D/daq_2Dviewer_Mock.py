from qtpy.QtCore import QThread, Slot, QRectF
from qtpy import QtWidgets
import numpy as np
import pymodaq.daq_utils.math_utils as mutils
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, main, comon_parameters
from easydict import EasyDict as edict
from collections import OrderedDict
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo, DataFromPlugins, Axis
from pymodaq.daq_utils.array_manipulation import crop_array_to_axis, crop_vector_to_axis


class DAQ_2DViewer_Mock(DAQ_Viewer_base):
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
        {'title': 'Nimages colors:', 'name': 'Nimagescolor', 'type': 'int', 'value': 1, 'default': 1, 'min': 0,
         'max': 3},
        {'title': 'Nimages pannels:', 'name': 'Nimagespannel', 'type': 'int', 'value': 1, 'default': 0, 'min': 0},
        {'title': 'Use ROISelect', 'name': 'use_roi_select', 'type': 'bool', 'value': False},
        {'title': 'Threshold', 'name': 'threshold', 'type': 'int', 'value': 1, 'min': 0},
        {'title': 'rolling', 'name': 'rolling', 'type': 'int', 'value': 1, 'min': 0},
        {'title': 'Nx', 'name': 'Nx', 'type': 'int', 'value': 100, 'default': 100, 'min': 1},
        {'title': 'Ny', 'name': 'Ny', 'type': 'int', 'value': 200, 'default': 200, 'min': 1},
        {'title': 'Amp', 'name': 'Amp', 'type': 'int', 'value': 20, 'default': 20, 'min': 1},
        {'title': 'x0', 'name': 'x0', 'type': 'slide', 'value': 50, 'default': 50, 'min': 0},
        {'title': 'y0', 'name': 'y0', 'type': 'float', 'value': 100, 'default': 100, 'min': 0},
        {'title': 'dx', 'name': 'dx', 'type': 'float', 'value': 20, 'default': 20, 'min': 1},
        {'title': 'dy', 'name': 'dy', 'type': 'float', 'value': 40, 'default': 40, 'min': 1},
        {'title': 'n', 'name': 'n', 'type': 'int', 'value': 1, 'default': 1, 'min': 1},
        {'title': 'amp_noise', 'name': 'amp_noise', 'type': 'float', 'value': 4, 'default': 0.1, 'min': 0},

        {'title': 'Cam. Prop.:', 'name': 'cam_settings', 'type': 'group', 'children': []},
    ]

    def ini_attributes(self):
        self.controller: str = None

        self.x_axis = None
        self.y_axis = None
        self.live = False
        self.ind_commit = 0
        self.ind_data = 0
        self._ROI = dict(position=[10, 10], size=[5, 5])

    @Slot(QRectF)
    def ROISelect(self, roi_pos_size: QRectF):
        self._ROI['position'] = int(roi_pos_size.left()), int(roi_pos_size.top())
        self._ROI['size'] = int(roi_pos_size.width()), int(roi_pos_size.height())

    def commit_settings(self
                        , param):
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
        x_axis = np.linspace(0, self.settings.child('Nx').value(), self.settings.child('Nx').value(),
                             endpoint=False)
        y_axis = np.linspace(0, self.settings.child('Ny').value(), self.settings.child('Ny').value(),
                             endpoint=False)
        data_mock = self.settings.child('Amp').value() * (
            mutils.gauss2D(x_axis, self.settings.child('x0').value(), self.settings.child('dx').value(),
                          y_axis, self.settings.child('y0').value(), self.settings.child('dy').value(),
                          self.settings.child('n').value())) + self.settings.child('amp_noise').value() * \
                    np.random.rand(len(y_axis), len(x_axis))

        for indy in range(data_mock.shape[0]):
            data_mock[indy, :] = data_mock[indy, :] * np.sin(x_axis / 4) ** 2
        data_mock = np.roll(data_mock, self.ind_data * self.settings.child('rolling').value(), axis=1)

        if self.settings['use_roi_select']:
            x_axis, y_axis, data = \
                crop_array_to_axis(x_axis, y_axis, data_mock,
                                   (self._ROI['position'][0], self._ROI['position'][0] + self._ROI['size'][0],
                                    self._ROI['position'][1], self._ROI['position'][1] + self._ROI['size'][1]))


            try:
                self.image[self._ROI['position'][1]:self._ROI['position'][1] + self._ROI['size'][1]+1,
                     self._ROI['position'][0]:self._ROI['position'][0] + self._ROI['size'][0]+1] = data

            except Exception as e:
                self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))
        else:

            self.image = data_mock

        self.ind_data += 1

        QThread.msleep(100)

        return self.image

    def ini_detector(self, controller=None):
        self.ini_detector_init(controller, "Mock controller")

        self.x_axis = self.get_xaxis()
        self.y_axis = self.get_yaxis()

        # initialize viewers with the future type of data but with 0value data
        self.data_grabed_signal_temp.emit(self.average_data(1, True))
        # OrderedDict(name='Mock3', data=[np.zeros((128,))], type='Data1D')])

        initialized = True
        info = 'Init'
        return info, initialized

    def close(self):
        """
            not implemented.
        """
        pass

    def get_xaxis(self):
        self.set_Mock_data()
        return self.x_axis

    def get_yaxis(self):
        self.set_Mock_data()
        return self.y_axis

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
        data_tmp = np.zeros_like(self.image)
        for ind in range(Naverage):
            data_tmp += self.set_Mock_data()
        data_tmp = data_tmp / Naverage

        data_tmp = data_tmp * (data_tmp >= self.settings['threshold']) * (init is False)
        for ind in range(self.settings['Nimagespannel']):
            datatmptmp = []
            for indbis in range(self.settings['Nimagescolor']):
                datatmptmp.append(data_tmp)
            data.append(DataFromPlugins(name='Mock2D_{:d}'.format(ind), data=datatmptmp, dim='Data2D'))
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
