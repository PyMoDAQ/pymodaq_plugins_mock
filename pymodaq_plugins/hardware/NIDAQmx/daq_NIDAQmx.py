from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSignal, QThread
from pymodaq.daq_utils.daq_utils import ThreadCommand, DataFromPlugins
import numpy as np
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base
from easydict import EasyDict as edict
from collections import OrderedDict
from enum import IntEnum
from pymodaq.daq_viewer.utility_classes import comon_parameters
import PyDAQmx
import ctypes
from pyqtgraph.parametertree import Parameter, ParameterTree, registerParameterType
import pyqtgraph.parametertree.parameterTypes as pTypes
import pymodaq.daq_utils.custom_parameter_tree as custom_tree

class DAQ_NIDAQ_source(IntEnum):
    """
        Enum class of NIDAQ_source

        =============== ==========
        **Attributes**   **Type**
        *Analog_Input*   int
        *Counter*        int
        =============== ==========
    """
    Analog_Input=0
    Counter=1
    Analog_Output=2
    @classmethod
    def names(cls):
        return [name for name, member in cls.__members__.items()]

class DAQ_analog_types(IntEnum):
    """
        Enum class of Ai types

        =============== ==========
        **Attributes**   **Type**
        =============== ==========
    """
    Voltage=PyDAQmx.DAQmx_Val_Voltage
    Current=PyDAQmx.DAQmx_Val_Current
    Thermocouple=PyDAQmx.DAQmx_Val_Temp_TC
    @classmethod
    def names(cls):
        return [name for name, member in cls.__members__.items()]

    @classmethod
    def values(cls):
        return [cls[name].value for name, member in cls.__members__.items()]

class DAQ_thermocouples(IntEnum):
    """
        Enum class of thermocouples type

        =============== ==========
        **Attributes**   **Type**
        =============== ==========
    """
    J=PyDAQmx.DAQmx_Val_J_Type_TC
    K=PyDAQmx.DAQmx_Val_K_Type_TC
    N=PyDAQmx.DAQmx_Val_N_Type_TC
    R=PyDAQmx.DAQmx_Val_R_Type_TC
    S=PyDAQmx.DAQmx_Val_S_Type_TC
    T=PyDAQmx.DAQmx_Val_T_Type_TC
    B=PyDAQmx.DAQmx_Val_B_Type_TC
    E=PyDAQmx.DAQmx_Val_E_Type_TC
    @classmethod
    def names(cls):
        return [name for name, member in cls.__members__.items()]

class DAQ_termination(IntEnum):
    """
        Enum class of thermocouples type

        =============== ==========
        **Attributes**   **Type**
        =============== ==========
    """
    Auto=PyDAQmx.DAQmx_Val_Cfg_Default
    RSE=PyDAQmx.DAQmx_Val_RSE
    NRSE=PyDAQmx.DAQmx_Val_NRSE
    Diff=PyDAQmx.DAQmx_Val_Diff
    Pseudodiff=PyDAQmx.DAQmx_Val_PseudoDiff

    @classmethod
    def names(cls):
        return [name for name, member in cls.__members__.items()]

class ScalableGroupAI(pTypes.GroupParameter):
    """
        |

        ================ =============
        **Attributes**    **Type**
        *opts*            dictionnary
        ================ =============

        See Also
        --------
        hardware.DAQ_Move_Stage_type
    """

    params =[{'title': 'AI type:', 'name': 'ai_type', 'type': 'list', 'values': DAQ_analog_types.names()},
                {'title': 'Voltages:', 'name': 'voltage_settings', 'type': 'group', 'children': [
                    {'title': 'Voltage Min:', 'name': 'volt_min', 'type': 'float', 'value': -10, 'suffix': 'V'},
                    {'title': 'Voltage Max:', 'name': 'volt_max', 'type': 'float', 'value': 10, 'suffix': 'V'},
                ]},
                {'title': 'Current:', 'name': 'current_settings', 'type': 'group', 'visible': False, 'children': [
                    {'title': 'Current Min:', 'name': 'curr_min', 'type': 'float', 'value': -1, 'suffix': 'A'},
                    {'title': 'Current Max:', 'name': 'curr_max', 'type': 'float', 'value': 1, 'suffix': 'A'},
                ]},
                {'title': 'Thermocouple:', 'name': 'thermoc_settings', 'type': 'group', 'visible': False, 'children': [
                    {'title': 'Thc. type:', 'name': 'thermoc_type', 'type': 'list', 'values': DAQ_thermocouples.names(),
                     'value': 'K'},
                    {'title': 'Temp. Min (°C):', 'name': 'T_min', 'type': 'float', 'value': 0, 'suffix': '°C'},
                    {'title': 'Temp. Max (°C):', 'name': 'T_max', 'type': 'float', 'value': 50, 'suffix': '°C'},
                ]},
                {'title': 'Termination:', 'name': 'termination', 'type': 'list', 'values': DAQ_termination.names()},
            ]

    def __init__(self, **opts):
        opts['type'] = 'groupai'
        opts['addText'] = "Add"
        opts['addList'] = opts['values']
        pTypes.GroupParameter.__init__(self, **opts)

    def addNew(self, typ):
        """
            Add a child.

            =============== ===========
            **Parameters**   **Type**
            *typ*            string
            =============== ===========
        """
        childnames=[par.name() for par in self.children()]
        if childnames==[]:
            newindex=0
        else:
            newindex=len(childnames)

        child={'title': typ ,'name': 'ai{:02.0f}'.format(newindex), 'type': 'group', 'children': self.params, 'removable':True, 'renamable':False}

        self.addChild(child)
registerParameterType('groupai', ScalableGroupAI, override=True)

class ScalableGroupCounter( pTypes.GroupParameter):
    """
        |

        ================ =============
        **Attributes**    **Type**
        *opts*            dictionnary
        ================ =============

        See Also
        --------
        hardware.DAQ_Move_Stage_type
    """

    params =[ {'title':'Edge type::', 'name': 'edge', 'type': 'list', 'values':['Rising', 'Falling']},]

    def __init__(self, **opts):
        opts['type'] = 'groupai'
        opts['addText'] = "Add"
        opts['addList'] = opts['values']
        pTypes.GroupParameter.__init__(self, **opts)

    def addNew(self, typ):
        """
            Add a child.

            =============== ===========
            **Parameters**   **Type**
            *typ*            string
            =============== ===========
        """
        childnames=[par.name() for par in self.children()]
        if childnames==[]:
            newindex=0
        else:
            newindex=len(childnames)

        child={'title': typ ,'name': 'counter{:02.0f}'.format(newindex), 'type': 'group', 'children': self.params, 'removable':True, 'renamable':False}

        self.addChild(child)
registerParameterType('groupcounter', ScalableGroupCounter, override=True)

class DAQ_NIDAQmx(DAQ_Viewer_base):
    """
        ==================== ========================
        **Attributes**         **Type**
        *data_grabed_signal*   instance of pyqtSignal
        *params*               dictionnary list
        *task*
        ==================== ========================

        See Also
        --------
        refresh_hardware
    """

    data_grabed_signal=pyqtSignal(list)
    import PyDAQmx

    params = comon_parameters+[
             {'title': 'Refresh hardware:', 'name': 'refresh_hardware', 'type': 'bool', 'value': False},
             {'title': 'Signal type:', 'name': 'NIDAQ_type', 'type': 'list', 'values': DAQ_NIDAQ_source.names()},

             {'title': 'AI Settings:', 'name': 'ai_settings', 'type': 'group', 'children':[
                 {'title':'Nsamples:', 'name': 'Nsamples', 'type': 'int', 'value': 1000, 'default': 1000, 'min':1},
                 {'title':'Frequency:', 'name': 'frequency', 'type': 'float', 'value': 1000, 'default': 1000, 'min': 0, 'suffix': 'Hz'},
                 {'title': 'AI Channels:', 'name': 'ai_channels', 'type': 'groupai', 'values': []},
                 ]},
             {'title': 'Counter Settings:', 'name': 'counter_settings', 'type': 'group', 'visible': False, 'children':[
                 {'title': 'Counting time (ms):', 'name': 'counting_time', 'type': 'float', 'value': 100, 'default': 100, 'min': 0},
                 {'title': 'Counting Channels:', 'name': 'counter_channels', 'type': 'groupcounter', 'values': []},
                 ]},
             ]


    def __init__(self, parent=None, params_state=None, control_type="0D"):
        super(DAQ_NIDAQmx, self).__init__(parent, params_state)

        self.control_type = control_type  # could be "0D", "1D"
        if self.control_type =="1D":
            self.settings.child(('NIDAQ_type')).setLimits(['Analog_Input'])
        else:
            self.settings.child(('NIDAQ_type')).setLimits(DAQ_NIDAQ_source.names())

        self.task=None
        self.refresh_hardware()
        self.timer= QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.counter_done)


    def commit_settings(self,param):
        """
            Activate the parameters changes in the hardware.

            =============== ================================ ===========================
            **Parameters**   **Type**                        **Description**
            *param*         instance of pyqtgraph.parameter   the parameter to activate
            =============== ================================ ===========================

            See Also
            --------
            update_NIDAQ_channels, update_task, DAQ_NIDAQ_source, refresh_hardware
        """
        # if param.name() == 'NIDAQ_devices':
        #     self.update_NIDAQ_channels()
        #     self.update_task()

        if param.name() == 'NIDAQ_type':
            self.update_NIDAQ_channels()
            if param.value() == DAQ_NIDAQ_source(0).name: #analog input
                self.settings.child(('ai_settings')).show()
                self.settings.child(('counter_settings')).hide()
            elif param.value() == DAQ_NIDAQ_source(1).name: #counter input
                self.settings.child(('ai_settings')).hide()
                self.settings.child(('counter_settings')).show()
            self.update_task()

        elif param.name() == 'refresh_hardware':
            if param.value():
                self.refresh_hardware()
                QtWidgets.QApplication.processEvents()
                self.settings.child(('refresh_hardware')).setValue(False)

        elif param.name() == 'ai_type':
            param.parent().child(('voltage_settings')).show(param.value() == 'Voltage')
            param.parent().child(('current_settings')).show(param.value() == 'Current')
            param.parent().child(('thermoc_settings')).show(param.value() == 'Thermocouple')
            self.update_task()

        else:
            self.update_task()


    @classmethod
    def update_NIDAQ_devices(cls):
        """
            Read and decode devices in the buffer.

            =============== ========= =================
            **Parameters**  **Type**   **Description**
            *cls*            ???
            =============== ========= =================

            Returns
            -------
            list
                list of devices
        """
        try:
            buff = cls.PyDAQmx.create_string_buffer(128)
            cls.PyDAQmx.DAQmxGetSysDevNames(buff, len(buff));
            devices = buff.value.decode().split(',')
            return devices
        except:
            return []


    def update_NIDAQ_channels(self,devices=None,type_signal=None):
        """
            Update the communication channels of the NIDAQ hardware.

            =============== ========== =======================
            **Parameters**   **Type**  **Description**
            *devices*         list(string)    the names of the devices
            *type_signal*    string    the type of the signal
            =============== ========== =======================

            See Also
            --------
            DAQ_NIDAQ_source, daq_utils.ThreadCommand
        """
        try:

            if devices is None:
                devices = self.update_NIDAQ_devices()

            if type_signal is None:
                type_signal = self.settings.child(('NIDAQ_type')).value()

            if devices != []:
                channels_tot = []
                for device in devices:
                    buff = self.PyDAQmx.create_string_buffer(1024)
                    if type_signal == DAQ_NIDAQ_source(0).name:  # analog input
                        self.PyDAQmx.DAQmxGetDevAIPhysicalChans(device, buff, len(buff))

                    elif type_signal == DAQ_NIDAQ_source(1).name:  # counter
                        self.PyDAQmx.DAQmxGetDevCIPhysicalChans(device, buff, len(buff))

                    channels = buff.value.decode()[:].split(',')
                    if channels != ['']:
                        channels_tot.extend(channels)

                if len(channels_tot) >= 1:

                    if type_signal == DAQ_NIDAQ_source(0).name:  # analog input
                        self.settings.child('ai_settings', 'ai_channels').setOpts(addList= channels_tot)
                    elif type_signal == DAQ_NIDAQ_source(1).name:  # counter
                        self.settings.child('counter_settings', 'counter_channels').setOpts(addList=channels_tot)

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status',[str(e),"log"]))

    @classmethod
    def DAQmxGetErrorString(cls, error_code):
        buffer = PyDAQmx.create_string_buffer(1024)
        cls.PyDAQmx.DAQmxGetErrorString(error_code, buffer, len(buffer))
        return buffer.value.decode()

    def refresh_hardware(self):
        """
            Refresh the NIDAQ hardware from settings values.

            See Also
            --------
            update_NIDAQ_devices, update_NIDAQ_channels
        """
        devices=self.update_NIDAQ_devices()
        self.update_NIDAQ_channels(devices)

    def update_task(self):
        """
            Update the current module task from settings parameters.

            See Also
            --------
            DAQ_NIDAQ_source, daq_utils.ThreadCommand
        """
        try:
            if self.task is not None:
                if type(self.task) == self.PyDAQmx.Task:
                    self.task.ClearTask()
                else: self.task = None

            self.task = self.PyDAQmx.Task()

            if self.settings.child(('NIDAQ_type')).value() == 'Analog_Input': #analog input
                channels = [child.opts['title'] for child in self.settings.child('ai_settings', 'ai_channels').children()]
                channels_name = [child.name() for child in self.settings.child('ai_settings', 'ai_channels').children()]

                for ind_channel, channel in enumerate(channels):
                    ai_type = self.settings.child('ai_settings', 'ai_channels', channels_name[ind_channel], 'ai_type').value()
                    termination = DAQ_termination[self.settings.child('ai_settings', 'ai_channels' ,
                                                            channels_name[ind_channel],'termination').value()].value

                    if ai_type == "Voltage":
                        err_code = self.task.CreateAIVoltageChan(channel, "",
                                     termination,
                                     self.settings.child('ai_settings', 'ai_channels' , channels_name[ind_channel], 'voltage_settings', 'volt_min').value(),
                                     self.settings.child('ai_settings', 'ai_channels' , channels_name[ind_channel], 'voltage_settings', 'volt_max').value(),
                                     self.PyDAQmx.DAQmx_Val_Volts, None)

                    elif ai_type == "Current":
                        err_code = self.task.CreateAICurrentChan(channel, "",
                                      termination,
                                      self.settings.child('ai_settings', 'ai_channels' , channels_name[ind_channel], 'current_settings', 'curr_min').value(),
                                      self.settings.child('ai_settings', 'ai_channels' , channels_name[ind_channel], 'current_settings', 'curr_max').value(),
                                      self.PyDAQmx.DAQmx_Val_Amps,
                                      self.PyDAQmx.DAQmx_Val_Internal,
                                      0., None)

                    elif ai_type == "Thermocouple":
                        err_code = self.task.CreateAIThrmcplChan(channel, "",
                                      self.settings.child('ai_settings', 'ai_channels' , channels_name[ind_channel],  'thermoc_settings', 'T_min').value(),
                                      self.settings.child('ai_settings', 'ai_channels' , channels_name[ind_channel],  'thermoc_settings', 'T_max').value(),
                                      self.PyDAQmx.DAQmx_Val_DegC,
                                      DAQ_thermocouples[self.settings.child('ai_settings', 'ai_channels' , channels_name[ind_channel], 'thermoc_settings', 'thermoc_type').value()].value,
                                      self.PyDAQmx.DAQmx_Val_BuiltIn, 0., "")

                    if err_code is None:
                        err_code=self.task.CfgSampClkTiming(None,self.settings.child('ai_settings','frequency').value(),self.PyDAQmx.DAQmx_Val_Rising,
                                                            self.PyDAQmx.DAQmx_Val_FiniteSamps,self.settings.child('ai_settings','Nsamples').value())

                        if err_code is not None:
                            status=self.DAQmxGetErrorString(err_code)
                            raise Exception(status)
                    else:
                        status=self.DAQmxGetErrorString(err_code)
                        raise Exception(status)

            elif self.settings.child(('NIDAQ_type')).value() == 'Counter': #counter
                channels = [child.opts['title'] for child in self.settings.child('counter_settings', 'counter_channels').children()]
                channels_name = [child.name() for child in self.settings.child('counter_settings', 'counter_channels').children()]
                for ind_channel, channel in enumerate(channels):
                    if self.settings.child('counter_settings', 'counter_channels', channels_name[ind_channel], 'edge').value()=="Rising":
                        edge=self.PyDAQmx.DAQmx_Val_Rising
                    else:
                        edge=self.PyDAQmx.DAQmx_Val_Falling
                    err_code=self.task.CreateCICountEdgesChan(channel,"",edge,0,self.PyDAQmx.DAQmx_Val_CountUp)
                    if err_code is not None:
                        status=self.DAQmxGetErrorString(err_code);raise Exception(status)

            self.status.initialized = True
            self.status.controller = self.task
        except Exception as e:
            self.status.info = str(e)
            self.status.initialized = True
            self.emit_status(ThreadCommand('Update_Status',[str(e),"log"]))

    def ini_detector(self, controller=None):
        """
            Initialisation procedure of the detector.

            See Also
            --------
            daq_utils.ThreadCommand
        """
        self.status.update(edict(initialized=False, info="", x_axis=None, y_axis=None, controller=None))
        try:
            if self.settings.child(('controller_status')).value() == "Slave":
                if controller is None:
                    raise Exception('no controller has been defined externally while this detector is a slave one')
                else:
                    self.task = controller
            else:
                self.update_task()
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [str(e), 'log']))
            self.status.info = str(e)
            self.status.initialized = False
            return self.status

    def close(self):
        """
            close the current module task.
        """
        self.task.StopTask()
        self.task.ClearTask()
        self.task=None


    def grab_data(self, Naverage=1, **kwargs):
        """
            | grab the current values with NIDAQ profile procedure.
            |
            | Send the data_grabed_signal once done.

            =============== ======== ===============================================
            **Parameters**  **Type**  **Description**
            *Naverage*      int       Number of values to average
            =============== ======== ===============================================

            See Also
            --------
            DAQ_NIDAQ_source
        """
        if self.settings.child(('NIDAQ_type')).value()==DAQ_NIDAQ_source(0).name: #analog input
            channels = [child.opts['title'] for child in self.settings.child('ai_settings', 'ai_channels').children()]
            data_tot = []
            read = self.PyDAQmx.int32()
            N=self.settings.child('ai_settings','Nsamples').value()
            data = np.zeros(N*len(channels), dtype=np.float64)
            #self.task.StartTask()
            self.task.ReadAnalogF64(self.PyDAQmx.DAQmx_Val_Auto,50.0,self.PyDAQmx.DAQmx_Val_GroupByChannel,data,len(data),self.PyDAQmx.byref(read),None)
            #self.task.StopTask()

            if self.control_type == "0D":
                for ind in range(len(channels)):
                    data_tot.append(np.array([np.mean(data[ind*N:(ind+1)*N])]))
                self.data_grabed_signal.emit([DataFromPlugins(name='NI AI', data=data_tot, dim='Data0D', labels=channels)])
            else:
                for ind in range(len(channels)):
                    data_tot.append(data[ind*N:(ind+1)*N])
                self.data_grabed_signal.emit([DataFromPlugins(name='NI AI', data=data_tot, dim='Data1D', labels=channels)])

        elif self.settings.child(('NIDAQ_type')).value()==DAQ_NIDAQ_source(1).name: #counter input

            self.task.StartTask()
            self.timer.start(self.settings.child('counter_settings','counting_time').value())





    def counter_done(self):

        channels = [child.opts['title'] for child in
                    self.settings.child('counter_settings', 'counter_channels').children()]
        data_counter = np.zeros(len(channels), dtype='uint32')
        read = self.PyDAQmx.int32()

        self.task.ReadCounterU32Ex(self.PyDAQmx.DAQmx_Val_Auto, 10.0, self.PyDAQmx.DAQmx_Val_GroupByChannel, data_counter,
                                   len(data_counter), self.PyDAQmx.byref(read), None)

        self.task.StopTask()
        data_counter = data_counter.astype(float)
        data_counter = data_counter / (self.settings.child('counter_settings', 'counting_time').value() * 1e-3)

        self.data_grabed_signal.emit([DataFromPlugins(name='NI Counter', data=[data_counter], dim='Data0D', labels=channels)])

    def stop(self):
        """
            not implemented.
        """
        try:
            self.task.StopTask()
        except:
            pass
        return ""
