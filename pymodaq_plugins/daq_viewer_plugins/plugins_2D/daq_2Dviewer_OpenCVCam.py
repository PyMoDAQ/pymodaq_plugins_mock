from PyQt5.QtCore import QThread
import numpy as np
import pymodaq.daq_utils.daq_utils as mylib
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base
from easydict import EasyDict as edict
from collections import OrderedDict
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo, DataFromPlugins, Axis
from pymodaq.daq_viewer.utility_classes import comon_parameters

from enum import IntEnum
import cv2


class OpenCVProp(IntEnum):
    # modes of the controlling registers (can be: auto, manual, auto single push, absolute Latter allowed with any other mode)
    # every feature can have only one mode turned on at a time
    CV_CAP_PROP_DC1394_OFF = -4  # turn the feature off (not controlled manually nor automatically)
    CV_CAP_PROP_DC1394_MODE_MANUAL = -3  # set automatically when a value of the feature is set by the user
    CV_CAP_PROP_DC1394_MODE_AUTO = -2
    CV_CAP_PROP_DC1394_MODE_ONE_PUSH_AUTO = -1
    CV_CAP_PROP_POS_MSEC = 0
    CV_CAP_PROP_POS_FRAMES = 1
    CV_CAP_PROP_POS_AVI_RATIO = 2
    CV_CAP_PROP_FRAME_WIDTH = 3
    CV_CAP_PROP_FRAME_HEIGHT = 4
    CV_CAP_PROP_FPS = 5
    CV_CAP_PROP_FOURCC = 6
    CV_CAP_PROP_FRAME_COUNT = 7
    CV_CAP_PROP_FORMAT = 8
    CV_CAP_PROP_MODE = 9
    CV_CAP_PROP_BRIGHTNESS = 10
    CV_CAP_PROP_CONTRAST = 11
    CV_CAP_PROP_SATURATION = 12
    CV_CAP_PROP_HUE = 13
    CV_CAP_PROP_GAIN = 14
    CV_CAP_PROP_EXPOSURE = 15
    CV_CAP_PROP_CONVERT_RGB = 16
    CV_CAP_PROP_WHITE_BALANCE_BLUE_U = 17
    CV_CAP_PROP_RECTIFICATION = 18
    CV_CAP_PROP_MONOCHROME = 19
    CV_CAP_PROP_SHARPNESS = 20
    CV_CAP_PROP_AUTO_EXPOSURE = 21  # exposure control done by camera
    # user can adjust reference level
    # using this feature
    CV_CAP_PROP_GAMMA = 22
    CV_CAP_PROP_TEMPERATURE = 23
    CV_CAP_PROP_TRIGGER = 24
    CV_CAP_PROP_TRIGGER_DELAY = 25
    CV_CAP_PROP_WHITE_BALANCE_RED_V = 26
    CV_CAP_PROP_ZOOM = 27
    CV_CAP_PROP_FOCUS = 28
    CV_CAP_PROP_GUID = 29
    CV_CAP_PROP_ISO_SPEED = 30
    CV_CAP_PROP_MAX_DC1394 = 31
    CV_CAP_PROP_BACKLIGHT = 32
    CV_CAP_PROP_PAN = 33
    CV_CAP_PROP_TILT = 34
    CV_CAP_PROP_ROLL = 35
    CV_CAP_PROP_IRIS = 36
    CV_CAP_PROP_SETTINGS = 37
    CV_CAP_PROP_BUFFERSIZE = 38
    CV_CAP_PROP_AUTOFOCUS = 39
    CV_CAP_PROP_SAR_NUM = 40
    CV_CAP_PROP_SAR_DEN = 41



    @classmethod
    def names(cls):
        names=cls.__members__.items()
        return [name for name, member in cls.__members__.items()]

class DAQ_2DViewer_OpenCVCam(DAQ_Viewer_base):
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

    params= comon_parameters+[{'title': 'Camera index:', 'name': 'camera_index', 'type': 'int', 'value': 0 , 'default':0, 'min': 0},
                              {'title': 'Colors:', 'name': 'colors', 'type': 'list', 'value': 'gray' , 'values': ['gray','RGB']},
                              {'title': 'Open Settings:', 'name': 'open_settings', 'type': 'bool', 'value': False },
                              {'title': 'Cam. Settings:', 'name': 'cam_settings', 'type': 'group', 'children': [
                              #     {'title': 'Autoexposure:', 'name': 'autoexposure', 'type': 'bool', 'value': False},
                              #     {'title': 'Exposure:', 'name': 'exposure', 'type': 'int', 'value': 0},
                              ]},
                              ]
    hardware_averaging = False

    def __init__(self, parent=None,
                 params_state=None):  # init_params is a list of tuple where each tuple contains info on a 1D channel (Ntps,amplitude, width, position and noise)
        super(DAQ_2DViewer_OpenCVCam, self).__init__(parent, params_state)
        self.x_axis = None
        self.y_axis = None





    def commit_settings(self,param):
        """
            Activate parameters changes on the hardware.

            =============== ================================ ===========================
            **Parameters**   **Type**                          **Description**
            *param*          instance of pyqtgraph Parameter   the parameter to activate
            =============== ================================ ===========================

            See Also
            --------
            
        """
        try:
            if param.name() == 'open_settings':
                if param.value():
                    self.controller.set(OpenCVProp['CV_CAP_PROP_SETTINGS'].value, 0)
                    #param.setValue(False)
            elif param.name() == 'colors':
                pass
            else:
                self.controller.set(OpenCVProp['CV_CAP_' + param.name()].value, param.value())
                val = self.controller.get(OpenCVProp['CV_CAP_' + param.name()].value)
                param.setValue(int(val))

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))

    def ini_detector(self, controller=None):
        """
            Initialisation procedure of the detector initializing the status dictionnary.

            See Also
            --------
            DAQ_utils.ThreadCommand, get_xaxis, get_yaxis
        """
        self.status.update(edict(initialized=False, info="", x_axis=None, y_axis=None, controller=None))
        try:

            if self.settings.child(('controller_status')).value() == "Slave":
                if controller is None:
                    raise Exception('no controller has been defined externally while this detector is a slave one')
                else:
                    self.controller = controller
            else:
                self.controller = cv2.VideoCapture(self.settings.child(('camera_index')).value())

            self.controller.set(OpenCVProp['CV_CAP_PROP_AUTO_EXPOSURE'].value, 1)
            self.get_active_properties() #to add settable settings to the param list (but driver builtin settings window is prefered (OpenCVProp['CV_CAP_PROP_SETTINGS'])

            self.x_axis = self.get_xaxis()
            self.y_axis = self.get_yaxis()

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

    def get_active_properties(self):
        props = OpenCVProp.names()
        self.additional_params = []
        for prop in props:
            try:
                ret = int(self.controller.get(OpenCVProp[prop].value))
                if ret != -1:
                    try:
                        ret_set = self.controller.set(OpenCVProp[prop].value, ret)
                    except:
                        ret_set = False
                    self.additional_params.append(
                        {'title': prop[7:], 'name': prop[7:], 'type': 'int', 'value': ret, 'readonly': not ret_set})
            except:
                pass
        self.settings.child('cam_settings').addChildren(self.additional_params)
        pass

    def close(self):
        """
            not implemented.
        """
        try:
            for child_dict in self.additional_params:
                self.settings.removeChild(self.settings.child((child_dict['name'])))
            self.controller.release()
        except:
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
            
        """
        Nx = int(self.controller.get(cv2.CAP_PROP_FRAME_WIDTH))  # property index corresponding to width
        self.x_axis = np.linspace(0, Nx - 1, Nx)
        return self.x_axis

    def get_yaxis(self):
        """
            Get the current y_axis from the Mock data setting.

            Returns
            -------
            1D numpy array
                the current y_axis.

            See Also
            --------
            
        """
        Ny = int(self.controller.get(cv2.CAP_PROP_FRAME_HEIGHT))  # property index corresponding to width
        self.y_axis = np.linspace(0, Ny - 1, Ny)
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
        if not self.controller.isOpened():
            self.controller.open(self.settings.child(('camera_index')).value())

        ret, frame = self.controller.read()
        # print(ret)
        # print(frame[:,:,0])
        # print(frame.shape)
        # QThread.msleep(500)

        if ret:
            if self.settings.child(('colors')).value() == 'gray':
                data_cam = [cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)]
                data_cam[0] = data_cam[0].astype(np.float32)
            else:
                if len(frame.shape) == 3:
                    data_cam = [frame[:, :, ind] for ind in range(frame.shape[2])]
                else:
                    data_cam = [cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)]

        else:
            data_cam = [np.zeros((len(self.y_axis), len(self.x_axis)))]
            self.emit_status(ThreadCommand('Update_Status', ['no return from the controller', 'log']))

        data = [DataFromPlugins(name='OpenCV', data=data_cam, dim='Data2D')]

        self.data_grabed_signal.emit(data)

    def stop(self):
        """
            not implemented.
        """

        return ""
