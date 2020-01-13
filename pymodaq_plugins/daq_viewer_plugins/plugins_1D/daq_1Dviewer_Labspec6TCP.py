from PyQt5.QtCore import QThread
from PyQt5 import QtWidgets
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base
import numpy as np
from easydict import EasyDict as edict
from collections import OrderedDict
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo, gauss1D, linspace_step
from pymodaq.daq_viewer.utility_classes import comon_parameters
from pyqtgraph.parametertree import Parameter, ParameterTree
import pyqtgraph.parametertree.parameterTypes as pTypes
import pymodaq.daq_utils.custom_parameter_tree as custom_tree
from pymodaq_plugins.hardware.horiba.labspec6 import Labspec6Client



class DAQ_1DViewer_Labspec6TCP(DAQ_Viewer_base):
    """
    1D viewer plugin Enabling communication with Labspec6 software controlling horiba spectrometers.
    Labspec must be opened and its AFM server turned on, see Labspec6 configuration
    """
    params = comon_parameters+[
            {'title': 'Connection', 'name': 'connection', 'type': 'group', 'children': [
                {'title': 'Controller', 'name': 'controllerid', 'type': 'str', 'value': '', 'readonly': True},
                {'title': 'IP', 'name': 'ip_address', 'type': 'str', 'value': 'localhost'},
                {'title': 'Port', 'name': 'port', 'type': 'int', 'value': 1234},
                ]
             },
            {'title': 'Acquisition Parameters', 'name': 'acq_params', 'type': 'group', 'children': [
                {'title': 'Spectro (nm)', 'name': 'wavelength', 'type': 'float', 'value': 0.0, 'min': 0.0},
                {'title': 'Exp. Time (s)', 'name': 'exposure', 'type': 'float', 'value': 1.0, 'min': 0.001},
                {'title': 'Accumulation', 'name': 'accumulations', 'type': 'int', 'value': 1, 'min': 1},
                {'title': 'Binning', 'name': 'binning', 'type': 'int', 'value': 1, 'min': 1},
                ]
             },
            {'title': 'Instrument setup', 'name': 'inst_setup', 'type': 'group', 'children': [
                {'title': 'Grating', 'name': 'grating', 'type': 'list', 'values': []},
                {'title': 'Laser', 'name': 'laser', 'type': 'list', 'values': []},
                {'title': 'Hole', 'name': 'hole', 'type': 'int', 'value': 70, 'min': 1},
                {'title': 'Slit', 'name': 'slit', 'type': 'int', 'value': 100, 'min': 1},
                ],
            },
    ]

    param_mapping = {'spectro_wl': 'Spectro', 'exposure': 'Exposure', 'accumulation': 'Accumulations',
                     'binning': 'Binning', 'grating': 'Grating', 'laser': 'Laser', 'hole': 'Hole', 'slit': 'Slit'}

    hardware_averaging = False

    def __init__(self, parent=None, params_state=None): #init_params is a list of tuple where each tuple contains info on a 1D channel (Ntps,amplitude, width, position and noise)
        self.controller = None
        super().__init__(parent, params_state)
        self.x_axis = dict(label='photon wavelength', unit='nm')
        self.sock = None
        self.controller_ready = False

    def commit_settings(self, param):
        """
            Setting the mock data

            ============== ========= =================
            **Parameters**  **Type**  **Description**
            *param*         none      not used
            ============== ========= =================

            See Also
            --------
            set_Mock_data
        """
        if param.name() == 'wavelength':
            self.controller.wavelength = param.value()
        elif param.name() == 'exposure':
            self.controller.exposure = param.value()
        elif param.name() == 'accumulations':
            self.controller.accumulations = param.value()
        elif param.name() == 'binning':
            self.controller.binning = param.value()
        elif param.name() == 'grating':
            self.controller.grating = param.value()
        elif param.name() == 'laser':
            self.controller.laser = param.value()
        elif param.name() == 'hole':
            self.controller.hole = param.value()
        elif param.name() == 'slit':
            self.controller.slit = param.value()

    def set_spectro_wl(self, spectro_wl):
        """
        Method related to spectrometer module, mandatory
        Parameters
        ----------
        spectro_wl: set the "grating" position

        """
        self.controller.wavelength = spectro_wl
        self.settings.child('acq_params', 'spectro_wl').setValue(spectro_wl)

        self.get_spectro_wl()

    def get_spectro_wl(self):
        """
        Method related to spectrometer module, mandatory
        Get the "grating" position
        """
        self.emit_status(ThreadCommand('spectro_wl', [self.controller.wavelength]))

    def get_laser_wl(self):
        """
        Method related to spectrometer module, mandatory if laser can be set
        Get the "laser" position
        """
        self.emit_status(ThreadCommand('laser_wl', [self.controller.laser]))

    def set_laser_wl(self, laser_wl):
        """
        Method related to spectrometer module, mandatory if laser can be set
        Set the "laser" position
        """
        self.controller.laser = laser_wl
        self.settings.child('inst_setup', 'laser').setValue(laser_wl)
        self.get_laser_wl()

    def set_exposure_ms(self, exposure):
        self.controller.exposure = exposure/1000
        self.settings.child('acq_params', 'exposure').setValue(exposure/1000)
        self.emit_status(ThreadCommand('exposure_ms', [self.controller.exposure*1000]))

    def ini_detector(self, controller=None):
        """
            Initialisation procedure of the detector updating the status dictionnary.

            See Also
            --------
            set_Mock_data, daq_utils.ThreadCommand
        """
        self.status.update(edict(initialized=False,info="",x_axis=None,y_axis=None,controller=None))
        try:

            if self.settings.child(('controller_status')).value()=="Slave":
                if controller is None: 
                    raise Exception('no controller has been defined externally while this detector is a slave one')
                else:
                    self.controller = controller
            else:
                self.controller = Labspec6Client()
                ret, data, extra = self.controller.connect(self.settings.child('connection', 'ip_address').value(),
                                                           self.settings.child('connection', 'port').value())
                if ret != 'OK':
                    raise IOError('Wrong return from Server')
                self.settings.child('connection',  'controllerid').setValue(data)

            self.init_params()

            # initialize viewers with the future type of data
            self.x_axis = self.controller.get_x_axis()

            self.data_grabed_signal_temp.emit([OrderedDict(name='LabSpec6', data=[self.x_axis*0], type='Data1D',
                x_axis=dict(data=self.x_axis, units='nm', label='Wavelength'), labels=['Spectrum']),])

            self.status.initialized = True
            self.status.controller = self.controller
            self.status.x_axis = self.x_axis
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))
            self.status.info = getLineInfo() + str(e)
            self.status.initialized = False
            return self.status

    def close(self):
        """
            Not implemented.
        """
        self.controller.close()

    def init_params(self):
        for child in self.settings.child(('acq_params')).children():
            data = getattr(self.controller, child.name())
            if data is not None:
                child.setValue(data)
            else:
                child.hide()

        child = self.settings.child('inst_setup', 'grating')
        ind, data = self.controller.get_gratings()
        if data is not None:
            child.setOpts(limits=data)
            child.setValue(data[ind])
        else:
            child.hide()

        child = self.settings.child('inst_setup', 'laser')
        ind, data = self.controller.get_lasers()
        if data is not None:
            child.setOpts(limits=data)
            child.setValue(data[ind])
        else:
            child.hide()

        child = self.settings.child('inst_setup', 'hole')
        data = self.controller.hole
        if data is not None:
            child.setValue(data)
        else:
            child.hide()

        child = self.settings.child('inst_setup', 'slit')
        data = self.controller.slit
        if data is not None:
            child.setValue(data)
        else:
            child.hide()

    def grab_data(self, Naverage=1, **kwargs):
        """
        """
        Naverage = 1
        if not self.controller_ready:
            ret = self.controller.prepare_one_acquisition()
            if ret == 'ready':
                self.controller_ready = True
            else:
                self.emit_status(ThreadCommand('Update_Status', ['Spectrometer not ready to grab data...', 'log']))
        if self.controller_ready:
            data = self.controller.grab_spectrum()
        else:
            data = self.controller.wavelength_axis * 0
        if data is None:
            self.emit_status(ThreadCommand('Update_Status', ['No data from spectrometer', 'log']))
            data = self.controller.wavelength_axis * 0
        self.data_grabed_signal.emit([OrderedDict(name='LabSpec6', data=[data], type='Data1D',
                            x_axis=dict(data=self.controller.wavelength_axis, units='nm', label='Wavelength'))])

    def stop(self):
        """
            not implemented.
        """
        
        return ""
