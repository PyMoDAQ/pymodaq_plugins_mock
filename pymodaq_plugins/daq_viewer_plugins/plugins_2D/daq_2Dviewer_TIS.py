"""
Plugin for the USb The Imaging Source cameras
Using the python wrapper pyicic
https://github.com/morefigs/py-ic-imaging-control
py-ic-imaging-control provides control of The Imaging Source (TIS) cameras using only Python. It is a Python wrapper for the IC Imaging Control SDK and wraps the tisgrabber.dll file included in the IC Imaging Control C SDK installer using ctypes. The code currently supports most of the functionality exposed by the DLL file, including frame ready callbacks.
This module only works on Windows due to wrapping a DLL. Tested on Windows 7 with GigE and USB The Imaging Source cameras.
"""

import os
from PyQt5.QtCore import QThread
from PyQt5 import QtWidgets
import numpy as np
import ctypes
import pymodaq.daq_utils.daq_utils as mylib
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base
from easydict import EasyDict as edict
from collections import OrderedDict
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo
from pymodaq.daq_viewer.utility_classes import comon_parameters
import pymodaq_plugins.hardware.TIS as TIS
libpath = os.path.split(TIS.__file__)[0]
if libpath not in os.environ['path']:
    os.environ['path'] += ';'+libpath

class DAQ_2DViewer_TIS(DAQ_Viewer_base):
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
    from pyicic import IC_ImagingControl

    ic = IC_ImagingControl.IC_ImagingControl()
    ic.init_library()
    cameras = [cam.decode() for cam in ic.get_unique_device_names()]


    params = comon_parameters+\
            [{'title': 'Cam. names:', 'name': 'cam_name', 'type': 'list', 'values': cameras},
             {'title': 'Video Formats:', 'name': 'video_formats', 'type': 'list'},
             {'title': 'Gray scale:', 'name': 'gray_scale', 'type': 'bool', 'value': False},
             {'title': 'Cam. Prop.:', 'name': 'cam_settings', 'type': 'group', 'children': [
                 {'title': 'Brightness:', 'name': 'brightness', 'type': 'int'},
                 {'title': 'Contrast:', 'name': 'contrast', 'type': 'int'},
                 {'title': 'Hue:', 'name': 'hue', 'type': 'int'},
                 {'title': 'Saturation:', 'name': 'saturation', 'type': 'int'},
                 {'title': 'Sharpness:', 'name': 'sharpness', 'type': 'int'},
                 {'title': 'Gamma:', 'name': 'gamma', 'type': 'int'},
                 {'title': 'Color?:', 'name': 'colorenable', 'type': 'bool'},
                 {'title': 'Whitebalance:', 'name': 'whitebalance', 'type': 'int'},
                 {'title': 'Black light compensation:', 'name': 'blacklightcompensation', 'type': 'int'},
                 {'title': 'Gain:', 'name': 'gain', 'type': 'int'},
                 {'title': 'Pan:', 'name': 'pan', 'type': 'int'},
                 {'title': 'Tilt:', 'name': 'tilt', 'type': 'int'},
                 {'title': 'Roll:', 'name': 'roll', 'type': 'int'},
                 {'title': 'Zoom:', 'name': 'zoom', 'type': 'int'},
                 {'title': 'Exposure:', 'name': 'exposure', 'type': 'int'},
                 {'title': 'Iris:', 'name': 'iris', 'type': 'int'},
                 {'title': 'Focus:', 'name': 'focus', 'type': 'int'},

                 ]},


            ]
    def __init__(self,parent=None,params_state=None): #init_params is a list of tuple where each tuple contains info on a 1D channel (Ntps,amplitude, width, position and noise)
        super(DAQ_2DViewer_TIS,self).__init__(parent,params_state)
        self.x_axis=None
        self.y_axis=None
        self.live=False

        from pyicic import IC_Structures
        GrabberHandlePtr = ctypes.POINTER(IC_Structures.GrabberHandle)
        # c function type for frame callback
        # outside of class so it can be called by unbound function
        callback = ctypes.WINFUNCTYPE(None, GrabberHandlePtr, ctypes.POINTER(ctypes.c_ubyte),
                                                    ctypes.c_ulong, ctypes.c_void_p)
        self.__data_ready = callback(self._data_ready)


    def _data_ready(self, handle_ptr, p_data, frame_num, data):
        dat = self.controller.get_image_data()
        data = np.array(dat[0][:],dtype=np.uint8)
        data = data.reshape((dat[2],dat[1],3))
        self.data_grabed_signal.emit([OrderedDict(name='TIS ', data=[data[:,:,0], data[:,:,1], data[:,:,2]], type='Data2D'),])



    def commit_settings(self,param):
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
        try:
            if param.parent().name() == 'cam_settings':
                getattr(self.controller, param.name()).value = param.value()
                param.setValue(getattr(self.controller, param.name()).value)
            elif param.name() == 'video_formats':
                self.controller.stop_live()
                self.controller.set_video_format(param.value().encode())
                # if 'Y' in param.value():
                #     self.controller.set_format(0)
                # else:
                #     self.controller.set_format(1)
                self.controller.start_live()
        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo()+ str(e), 'log']))





    def ini_detector(self, controller=None):
        """
            Initialisation procedure of the detector initializing the status dictionnary.

            See Also
            --------
            daq_utils.ThreadCommand, get_xaxis, get_yaxis
        """
        self.status.update(edict(initialized=False,info="",x_axis=None,y_axis=None,controller=None))
        try:

            if self.settings.child(('controller_status')).value()=="Slave":
                if controller is None: 
                    raise Exception('no controller has been defined externally while this detector is a slave one')
                else:
                    self.controller=controller
            else:

                self.controller=self.ic.get_device(self.settings.child(('cam_name')).value().encode())
                self.controller.open()

            properties = self.controller.list_property_names()
            for prop in properties:
                if prop in [child.name() for child in self.settings.child(('cam_settings')).children()]:
                    if getattr(self.controller,prop).available:
                        param = self.settings.child('cam_settings',prop)
                        if param.opts['type'] =='int' or param.opts['type'] =='float':
                            range = getattr(self.controller,prop).range
                            param.setOpts(limits=range)
                        try:
                            getattr(self.controller, prop).auto = False
                        except:
                            pass
                        value = getattr(self.controller,prop).value
                        param.setValue(value)
                    else:
                        self.settings.child('cam_settings',prop).hide()

            formats = [form.decode() for form in self.controller.list_video_formats()]# if 'RGB'.encode() in form]
            self.settings.child(('video_formats')).setOpts(limits=formats)
            self.settings.child(('video_formats')).setValue(formats[8])
            self.controller.set_video_format(formats[8].encode())        # use first available video format

            self.controller.enable_continuous_mode(True)  # image in continuous mode
            self.controller.start_live(show_display=False)  # start imaging
            self.controller.enable_trigger(True)  # camera will wait for trigger

            if not self.controller.callback_registered:
                self.controller.register_frame_ready_callback(self.__data_ready)  # needed to wait for frame ready callback

            self.controller.send_trigger()


            self.x_axis=self.get_xaxis()
            self.y_axis=self.get_yaxis()

            # initialize viewers with the future type of data
            self.data_grabed_signal_temp.emit([OrderedDict(name='TIS', data=[np.zeros((len(self.y_axis),len(self.x_axis)))], type='Data2D'),])


            self.status.x_axis=self.x_axis
            self.status.y_axis=self.y_axis
            self.status.initialized=True
            self.status.controller=self.controller
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status',[getLineInfo()+ str(e),'log']))
            self.status.info=getLineInfo()+ str(e)
            self.status.initialized=False
            return self.status




    def close(self):
        """
            not implemented.
        """
        self.controller.stop_live()
        self.controller.close()

        self.ic.close_library()

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
        Nx = self.controller.get_video_format_width()
        self.x_axis= np.linspace(0,Nx-1,Nx,dtype=np.int32)
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
            set_Mock_data
        """
        Ny = self.controller.get_video_format_height()
        self.y_axis= np.linspace(0,Ny-1,Ny,dtype=np.int32)
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
        #self.controller.reset_frame_ready()
        if not self.controller.is_live():
            self.controller.enable_continuous_mode(True)  # image in continuous mode
            self.controller.start_live(show_display=False)  # start imaging
            self.controller.enable_trigger(True)

        self.controller.send_trigger()
        #self.controller.wait_til_frame_ready(1000)
        #self.controller.snap_image()



    def stop(self):
        """
            not implemented.
        """
        self.controller.stop_live()
        return ""

# if __name__ == '__main__':
#     from pyicic.IC_ImagingControl import *
#     # open lib
#     ic_ic = IC_ImagingControl()
#     ic_ic.init_library()
#
#     # open first available camera device
#     cam_names = ic_ic.get_unique_device_names()
#     cam = ic_ic.get_device(cam_names[0])
#     cam.open()
#     # change camera properties
#     cam.list_property_names()  # ['gain', 'exposure', 'hue', etc...]
#     cam.gain.auto = True  # enable auto gain
#     emin = cam.exposure.min  # 0
#     emax = cam.exposure.max  # 10
#     cam.exposure.value =int((emin + emax) / 2)  # disables auto exposure and sets value to half of range
#     # change camera settings
#     formats = cam.list_video_formats()
#     cam.set_video_format(formats[8])
#
#     pass