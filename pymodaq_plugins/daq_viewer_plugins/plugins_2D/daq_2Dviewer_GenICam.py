"""
Created on Thu Apr 25 16:13:29 2019
This plugin use the general standardized GeniCAM interface through the harvester package: https://github.com/genicam/harvesters
It will be working with any camera that is GeniCAM compliant and provides a GenTL (Transport Layer) through a *.cti dll file
So far it has been tested with Omron Sentech USB cameras, however harvesters is used with many camera and manufacturer.
For best use, don't use the manufaturer gentl file but the one provided by MatrixVision :
https://www.matrix-vision.com/software-drivers-en.html
**mvGenTL_acquire**
Once installed, activate your camera using mvDeviceConfigure

@author: Sébastien Weber
"""

import time
import os
from PyQt5.QtCore import QThread
from PyQt5 import QtWidgets
import numpy as np
import ctypes
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base
import pymodaq.daq_utils.custom_parameter_tree as custom_tree
from easydict import EasyDict as edict
from collections import OrderedDict
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo, recursive_find_files_extension, DataFromPlugins, Axis
from pymodaq.daq_utils.gui_utils import select_file, ListPicker
from pymodaq.daq_viewer.utility_classes import comon_parameters
from harvesters.core import Harvester
from harvesters.util.pfnc import mono_location_formats, \
    rgb_formats, bgr_formats, \
    rgba_formats, bgra_formats
try:
    cti_paths = recursive_find_files_extension(r'C:\Program Files\MATRIX VISION\mvIMPACT Acquire\bin\x64', 'cti')

except:
    cti_paths=[]

from enum import IntEnum

class EInterfaceType(IntEnum):
    """
    typedef for interface type
    """
    intfIValue = 0       #: IValue interface
    intfIBase = 1        #: IBase interface
    intfIInteger = 2     #: IInteger interface
    intfIBoolean = 3     #: IBoolean interface
    intfICommand = 4     #: ICommand interface
    intfIFloat = 5       #: IFloat interface
    intfIString = 6      #: IString interface
    intfIRegister = 7    #: IRegister interface
    intfICategory = 8    #: ICategory interface
    intfIEnumeration = 9 #: IEnumeration interface
    intfIEnumEntry = 10   #: IEnumEntry interface
    intfIPort       = 11  #: IPort interface

class DAQ_2DViewer_GenICam(DAQ_Viewer_base):
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
    harv = Harvester()


    for path in cti_paths:
        harv.add_cti_file(path)
        harv.update_device_info_list()
    devices = harv.device_info_list
    devices_names = [device.model for device in devices]

    params = comon_parameters+\
            [{'title': 'Cam. names:', 'name': 'cam_name', 'type': 'list', 'values': devices_names},
             {'title': 'Cam. Prop.:', 'name': 'cam_settings', 'type': 'group', 'children': []},
            ]

    def __init__(self,parent=None,params_state=None): #init_params is a list of tuple where each tuple contains info on a 1D channel (Ntps,amplitude, width, position and noise)
        super(DAQ_2DViewer_GenICam,self).__init__(parent,params_state)
        self.x_axis=None
        self.y_axis=None
        self.grabbing = False

        self.width = None
        self.width_max = None
        self.height = None
        self.height_max = None

        self.data = None

    def emit_data(self):
        if self.grabbing:
            with self.controller.fetch_buffer() as buffer:
                payload = buffer.payload
                component = payload.components[0]
                width = component.width
                height = component.height
                data_format = component.data_format

                if self.settings.child('ROIselect', 'use_ROI').value():
                    offsetx = self.controller.device.node_map.get_node('OffsetX').value
                    offsety = self.controller.device.node_map.get_node('OffsetY').value
                else:
                    offsetx = 0
                    offsety = 0

                if data_format in mono_location_formats:
                    data_tmp = component.data.reshape(height, width)
                    self.data[offsety:offsety+height, offsetx:offsetx+width] = data_tmp
                    self.data_grabed_signal.emit(
                        [DataFromPlugins(name='GenICam ', data=[self.data], dim='Data2D'), ])
                else:
                    # The image requires you to reshape it to draw it on the canvas:
                    if data_format in rgb_formats or \
                            data_format in rgba_formats or \
                            data_format in bgr_formats or \
                            data_format in bgra_formats:
                        #
                        content = component.data.reshape(height, width, int(component.num_components_per_pixel)  # Set of R, G, B, and Alpha
                        )
                        #
                        if data_format in bgr_formats:
                            # Swap every R and B:
                            content = content[:, :, ::-1]
                    self.data_grabed_signal.emit(
                        [DataFromPlugins(name='GenICam ', data=[self.data[:,:,ind] for ind in range(min(3,component.num_components_per_pixel))], dim='Data2D'), ])

                self.grabbing = False



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
            if param.name() in custom_tree.iter_children(self.settings.child(('cam_settings')),[]):

                self.stop()
                while self.controller.is_acquiring_images:
                    self.stop()
                    QtWidgets.QApplication.processEvents()

                feature = self.controller.device.node_map.get_node(param.name())
                interface_type = feature.node.principal_interface_type
                if interface_type == EInterfaceType.intfIInteger:
                    val = int((param.value()//param.opts['step'])*param.opts['step'])
                else:
                    val = param.value()
                feature.value = val #set the desired value
                param.setValue(feature.value) # retrieve the actually set one

                #self.update_features()


                if param.name() in ['Height', 'Width', 'OffsetX', 'OffsetY']:
                    if param.name() in ['Height', 'Width'] and not self.settings.child('ROIselect', 'use_ROI').value():
                        self.width = self.controller.device.node_map.get_node('Width').value
                        self.height = self.controller.device.node_map.get_node('Height').value


                        self.data = np.zeros((self.height, self.width))



            if param.name() in custom_tree.iter_children(self.settings.child(('ROIselect')),[]):

                while self.controller.is_acquiring_images:
                    QThread.msleep(50)
                    self.stop()
                    QtWidgets.QApplication.processEvents()

                self.set_ROI()

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo()+ str(e), 'log']))

    def set_ROI(self):
        params = custom_tree.iter_children_params(self.settings.child(('cam_settings')), [])
        param_names = [param.name() for param in params]

        if self.settings.child('ROIselect', 'use_ROI').value():
            #one starts by settings width and height so that offset could be set accordingly
            param = self.settings.child('ROIselect','width')
            param_to_set = params[param_names.index('Width')]
            step = param_to_set.opts['step']
            val = int((param.value() // step) * step)
            param_to_set.setValue(val)
            self.controller.device.node_map.get_node('Width').value = val

            param = self.settings.child('ROIselect', 'height')
            param_to_set = params[param_names.index('Height')]
            step = param_to_set.opts['step']
            val = int((param.value() // step) * step)
            param_to_set.setValue(val)
            self.controller.device.node_map.get_node('Height').value = val


            param = self.settings.child('ROIselect', 'x0')
            param_to_set = params[param_names.index('OffsetX')]
            step = param_to_set.opts['step']
            val = int((param.value() // step) * step)
            param_to_set.setValue(val)
            self.controller.device.node_map.get_node('OffsetX').value = val

            param = self.settings.child('ROIselect', 'y0')
            param_to_set = params[param_names.index('OffsetY')]
            step = param_to_set.opts['step']
            val = int((param.value() // step) * step)
            param_to_set.setValue(val)
            self.controller.device.node_map.get_node('OffsetY').value = val

        else:
            # one starts by settings offsets so that width and height could be set accordingly
            param_to_set = params[param_names.index('OffsetX')]
            val = 0
            param_to_set.setValue(val)
            self.controller.device.node_map.get_node('OffsetX').value = val

            param_to_set = params[param_names.index('OffsetY')]
            val = 0
            param_to_set.setValue(val)
            self.controller.device.node_map.get_node('OffsetY').value = val

            param_to_set = params[param_names.index('Width')]
            val = self.width_max
            param_to_set.setValue(val)
            self.controller.device.node_map.get_node('Width').value = val


            param_to_set = params[param_names.index('Height')]
            val = self.height_max
            param_to_set.setValue(val)
            self.controller.device.node_map.get_node('Height').value = val



    def get_features(self):
        features = self.controller.device.node_map.Root.features
        # self.newsettings = Parameter.create(name='cam_settingsd', type='group', children=self.populate_settings(features))
        #self.send_param_status(self.settings.child(('cam_settings')),[(self.settings.child(('cam_settings')),'childAdded', self.newsettings)])
        self.settings.child(('cam_settings')).addChildren(self.populate_settings(features))

    def update_features(self):
        #start = time.perf_counter()
        for child in custom_tree.iter_children_params(self.settings.child(('cam_settings')),[]):
            try:
                if self.controller.device.node_map.get_node(child.name()).get_access_mode() == 0:
                    child.setOpts(visible=False)
                elif self.controller.device.node_map.get_node(child.name()).get_access_mode() in [1, 3]:
                    child.setOpts(enabled=False)
                else:
                    child.setOpts(visible=True)
                    child.setOpts(enabled=True)
                child.setValue(self.controller.device.node_map.get_node(child.name()).value)
            except Exception as e:
                pass
        #print(time.perf_counter()-start)



    def populate_settings(self, features, param_list=[]):
        for feature in features:
            try:
                if feature.node.visibility == 0: #parameters for "beginners"
                    interface_type = feature.node.principal_interface_type
                    item = {}
                    if interface_type == EInterfaceType.intfIBoolean:
                        item.update({'type': 'bool', 'value': True if feature.value.lower() == 'true' else False,
                                     'readonly': feature.get_access_mode() in [0, 1, 3],
                                     'enabled':  not(feature.get_access_mode() in [0, 1, 3])})
                    elif interface_type == EInterfaceType.intfIFloat:
                        item.update({'type': 'float', 'value': feature.value,
                                     'readonly': feature.get_access_mode() in [0, 1, 3],
                                     'enabled': not (feature.get_access_mode() in [0, 1, 3]),
                                     'min': feature.min,
                                     'max': feature.max})
                    elif interface_type == EInterfaceType.intfIInteger:
                        item.update({'type': 'int', 'value': feature.value,
                                     'step': feature.inc,
                                     'readonly': feature.get_access_mode() in [0, 1, 3],
                                     'enabled': not (feature.get_access_mode() in [0, 1, 3]),
                                     'min': feature.min,
                                     'max': feature.max})
                        #print(feature.node.name)
                    elif interface_type == EInterfaceType.intfIString:
                        item.update({'type': 'str', 'value': feature.value,
                                     'readonly': feature.get_access_mode() in [0, 1, 3],
                                     'enabled': not(feature.get_access_mode() in [0, 1, 3])
                                     })

                    elif interface_type == EInterfaceType.intfIEnumeration:
                        item.update({'type': 'list', 'value': feature.value,
                                     'values': [f.node.display_name for f in feature.entries],
                                     'readonly': feature.get_access_mode() in [0, 1, 3],
                                     'enabled': not(feature.get_access_mode() in [0, 1, 3])
                                     })

                    elif interface_type == EInterfaceType.intfICategory:
                        new_list = []
                        item.update({'type': 'group', 'children': self.populate_settings(feature.node.children, new_list)})
                    else:
                        continue
                    item.update({'title': feature.node.display_name, 'name': feature.node.name, 'tooltip': feature.node.description})
                    param_list.append(item)
            except:
                pass

        return param_list


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
                if cti_paths == []:
                    file = select_file(start_path=r'C:\Program Files', save=False, ext='cti')
                    if file != '':
                        cti_paths.append(str(file))
                    for path in cti_paths:
                        self.harv.add_cti_file(path)
                        self.harv.update_device_info_list()
                    devices = self.harv.device_info_list
                    devices_names = [device.model for device in devices]
                    #device = QtWidgets.QInputDialog.getItem(None, 'Pick an item', 'List of discovered cameras:', devices_names, editable = False)

                    self.settings.child(('cam_name')).setLimits(devices_names)
                    self.settings.child(('cam_name')).setValue(devices_names[0])
                    QtWidgets.QApplication.processEvents()

                self.controller = self.harv.create_image_acquirer(model=self.settings.child(('cam_name')).value())
                self.controller.num_buffers = 2
                self.controller.device.node_map.get_node('OffsetX').value = 0
                self.controller.device.node_map.get_node('OffsetY').value = 0
                self.controller.device.node_map.get_node('Width').value = self.controller.device.node_map.get_node('Width').max
                self.controller.device.node_map.get_node('Height').value = self.controller.device.node_map.get_node('Height').max
                self.get_features()


            self.controller.on_new_buffer_arrival = self.emit_data

            self.x_axis=self.get_xaxis()
            self.y_axis=self.get_yaxis()

            self.width_max = self.controller.device.node_map.get_node('Width').max
            self.width = self.controller.device.node_map.get_node('Width').value
            self.height_max = self.controller.device.node_map.get_node('Height').max
            self.height = self.controller.device.node_map.get_node('Height').value
            self.data = np.zeros((self.height, self.width))
            # initialize viewers with the future type of data
            self.data_grabed_signal_temp.emit([DataFromPlugins(name='GenICam', data=[self.data], dim='Data2D'),])


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
        self.stop()

        self.controller.destroy()
        self.harv.reset()

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
        Nx = self.controller.device.node_map.get_node('Width').value
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
        Ny = self.controller.device.node_map.get_node('Height').value
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
        self.grabbing = True

        if not self.controller.is_acquiring_images:
            self.controller.start_image_acquisition()


    def stop(self):
        """
            not implemented.
        """
        ind = 0
        while self.controller.is_acquiring_images and ind < 10:
            try:
                self.controller.stop_image_acquisition()

            except Exception as e:
                pass
            QThread.msleep(500)
            print('stopping acquisition')

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