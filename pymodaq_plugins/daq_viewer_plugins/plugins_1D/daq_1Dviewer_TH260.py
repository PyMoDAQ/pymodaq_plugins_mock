from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, QThread, QTimer, QMutex, QMutexLocker
import numpy as np
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base
from easydict import EasyDict as edict
from collections import OrderedDict
from pymodaq.daq_utils.daq_utils import ThreadCommand
from enum import IntEnum
import ctypes
from pymodaq.daq_viewer.utility_classes import comon_parameters
from pymodaq_plugins.hardware.picoquant import timeharp260
from pymodaq.daq_utils.plotting.viewer0D.viewer0D_main import Viewer0D


class DAQ_1DViewer_TH260(DAQ_Viewer_base):
    """
        See Also
        --------
        utility_classes.DAQ_Viewer_base
    """
    params= comon_parameters+[
            {'title': 'Device index:', 'name': 'device', 'type': 'int', 'value': 0, 'max': 3, 'min': 0},
            {'title': 'Infos:', 'name': 'infos', 'type': 'str', 'value': "", 'readonly': True},
            {'title': 'Line Settings:', 'name': 'line_settings', 'type': 'group', 'expanded': False, 'children': [
                {'title': 'Sync Settings:', 'name': 'sync_settings', 'type': 'group', 'expanded': True, 'children': [
                    {'title': 'ZeroX (mV):', 'name': 'zerox', 'type': 'int', 'value': -10, 'max': 0, 'min': -40},
                    {'title': 'Level (mV):', 'name': 'level', 'type': 'int', 'value': -50, 'max': 0, 'min': -1200},
                    {'title': 'Offset (ps):', 'name': 'offset', 'type': 'int', 'value': 0, 'max': 99999, 'min': -99999},
                    {'title': 'Divider:', 'name': 'divider', 'type': 'list', 'value': 1, 'values': [1, 2, 4, 8]},
                ]},
                {'title': 'CH1 Settings:', 'name': 'ch1_settings', 'type': 'group', 'expanded': True, 'children': [
                    {'title': 'Enabled?:', 'name': 'enabled', 'type': 'bool', 'value': True},
                    {'title': 'ZeroX (mV):', 'name': 'zerox', 'type': 'int', 'value': -10, 'max': 0, 'min': -40},
                    {'title': 'Level (mV):', 'name': 'level', 'type': 'int', 'value': -150, 'max': 0, 'min': -1200},
                    {'title': 'Offset (ps):', 'name': 'offset', 'type': 'int', 'value': 0, 'max': 99999, 'min': -99999},
                    {'title': 'Deadtime (ns):', 'name': 'deadtime', 'type': 'list', 'value': 24, 'values': [24, 44, 66, 88, 112, 135, 160, 180]},

                ]},
                {'title': 'CH2 Settings:', 'name': 'ch2_settings', 'type': 'group', 'expanded': True, 'children': [
                    {'title': 'Enabled?:', 'name': 'enabled', 'type': 'bool', 'value': False},
                    {'title': 'ZeroX (mV):', 'name': 'zerox', 'type': 'int', 'value': -10, 'max': 0, 'min': -40},
                    {'title': 'Level (mV):', 'name': 'level', 'type': 'int', 'value': -150, 'max': 0, 'min': -1200},
                    {'title': 'Offset (ps):', 'name': 'offset', 'type': 'int', 'value': 0, 'max': 99999, 'min': -99999},
                    {'title': 'Deadtime (ns):', 'name': 'deadtime', 'type': 'list', 'value': 24, 'values': [24, 44, 66, 88, 112, 135, 160, 180]},
                ]},
             ]},
             {'title': 'Acquisition:', 'name': 'acquisition', 'type': 'group', 'expanded': True, 'children': [
                 {'title': 'Acq. type:', 'name': 'acq_type', 'type': 'list',
                                'value': 'Histo', 'values': ['Counting', 'Histo', 'FLIM']},
                 {'title': 'Acq. time (s):', 'name': 'acq_time', 'type': 'int', 'value': 1, 'min': 0.1,
                                    'max': 360000},
                 {'title': 'Elapsed time (s):', 'name': 'elapsed_time', 'type': 'int', 'value': 0, 'min': 0,
                                    'readonly': True},

                 {'title': 'Timings:', 'name': 'timings', 'type': 'group', 'expanded': True, 'children': [
                     {'title': 'Mode:', 'name': 'timing_mode', 'type': 'list', 'value': 'Hires', 'values': ['Hires', 'Lowres']},
                     {'title': 'Base Resolution (ps):', 'name': 'base_resolution', 'type': 'float', 'value': 25, 'min': 0, 'readonly': True},
                     {'title': 'Resolution (ns):', 'name': 'resolution', 'type': 'float', 'value': 0.2, 'min': 0},
                     {'title': 'Time window (s):', 'name': 'window', 'type': 'float', 'value': 100, 'min': 0, 'readonly': True, 'enabled': False, 'siPrefix': True},
                     {'title': 'Nbins:', 'name': 'nbins', 'type': 'list', 'value': 2048 , 'values': [1024*(2**lencode) for lencode in range(6)]},
                     {'title': 'Offset (ns):', 'name': 'offset', 'type': 'int', 'value': 0, 'max': 100000000, 'min': 0},
                 ]},

                 {'title': 'Rates:', 'name': 'rates', 'type': 'group', 'expanded': True, 'children': [
                     {'title': 'Show large display?', 'name': 'large_display', 'type': 'bool', 'value': False},
                     {'title': 'Sync rate (cts/s):', 'name': 'syncrate', 'type': 'int', 'value': 0, 'min': 0, 'readonly': True, 'siPrefix': True},
                     {'title': 'CH1 rate (cts/s):', 'name': 'ch1_rate', 'type': 'int', 'value': 0, 'min': 0, 'readonly': True, 'siPrefix': True},
                     {'title': 'CH2 rate (cts/s):', 'name': 'ch2_rate', 'type': 'int', 'value': 0, 'min': 0, 'readonly': True, 'siPrefix': True},
                     {'title': 'Nrecords:', 'name': 'records', 'type': 'int', 'value': 0, 'min': 0, 'readonly': True,  'siPrefix': True},
                 ]},
                 {'title': 'Markers:', 'name': 'markers', 'type': 'group', 'expanded': True, 'visible': True, 'children': [
                     {'title': 'Marker1:', 'name': 'marker1', 'type': 'group', 'expanded': True, 'children': [
                         {'title': 'Enabled?:', 'name': 'enabled', 'type': 'bool', 'value': True},
                         {'title': 'type:', 'name': 'type', 'type': 'list', 'value': 'Falling', 'values': ['Falling', 'Rising']},
                     ]},
                     {'title': 'Marker2:', 'name': 'marker2', 'type': 'group', 'expanded': True, 'children': [
                         {'title': 'Enabled?:', 'name': 'enabled', 'type': 'bool', 'value': True},
                         {'title': 'type:', 'name': 'type', 'type': 'list', 'value': 'Falling',
                          'values': ['Falling', 'Rising']},
                     ]},
                     {'title': 'Marker3:', 'name': 'marker3', 'type': 'group', 'expanded': True, 'children': [
                         {'title': 'Enabled?:', 'name': 'enabled', 'type': 'bool', 'value': True},
                         {'title': 'type:', 'name': 'type', 'type': 'list', 'value': 'Falling',
                          'values': ['Falling', 'Rising']},
                     ]},
                     {'title': 'Marker 4:', 'name': 'marker4', 'type': 'group', 'expanded': True, 'children': [
                         {'title': 'Enabled?:', 'name': 'enabled', 'type': 'bool', 'value': True},
                         {'title': 'type:', 'name': 'type', 'type': 'list', 'value': 'Falling',
                          'values': ['Falling', 'Rising']},
                     ]},
                 ]},
             ]},
            ]

    hardware_averaging = False

    def __init__(self, parent=None, params_state=None):

        super(DAQ_1DViewer_TH260,self).__init__(parent, params_state) #initialize base class with commom attributes and methods

        self.device = None
        self.x_axis = None
        self.controller = None
        self.datas = None #list of numpy arrays, see set_acq_mode
        self.data_pointers = None #list of ctypes pointers pointing to self.datas array elements, see set_acq_mode
        self.acq_done = False
        self.Nchannels = 0
        self.channels_enabled = {'CH1': {'enabled': True, 'index': 0}, 'CH2': {'enabled': False, 'index': 1}}
        self.modes = ['Histo', 'T2', 'T3']
        self.actual_mode = 'Counting'

    def commit_settings(self, param):
        """
            | Activate parameters changes on the hardware from parameter's name.
            |

            =============== ================================    =========================
            **Parameters**   **Type**                           **Description**
            *param*          instance of pyqtgraph parameter    The parameter to activate
            =============== ================================    =========================

            Three profile of parameter :
                * **bin_x** : set binning camera from bin_x parameter's value
                * **bin_y** : set binning camera from bin_y parameter's value
                * **set_point** : Set the camera's temperature from parameter's value.

        """
        try:
            if param.name() == 'acq_type':
                self.set_acq_mode(param.value())

            elif param.name() == 'nbins' or param.name() == 'resolution':
                self.set_get_resolution(param.name())

            elif param.name() == 'timing_mode':
                self.set_get_resolution('resolution')

            elif param.parent().name() == 'ch1_settings' or param.parent().name() == 'ch2_settings' or param.parent().name() == 'sync_settings':
                self.set_sync_channel(param)

            elif param.name() == 'offset' and param.parent().name() == 'timings':
                self.controller.TH260_SetOffset(self.device, param.value())

            elif param.name() == 'large_display' and param.value():
                self.emit_status(ThreadCommand('init_lcd', [dict(labels=['Syn. Rate (kcts/s)',
                                  'CH1 rate (kcts/s)', 'CH2 Rate (kcts/s)'], Nvals=3, digits=6)]))

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status',[str(e),'log']))


    def emit_data(self):
        """
        """
        try:
            print('emit')
            #lock = QMutexLocker(self.locker)
            mode = self.settings.child('acquisition', 'acq_type').value()
            if mode == 'Counting':
                rates = self.get_rates()
                self.data_grabed_signal.emit([OrderedDict(name='TH260', data=rates[1:], type='Data0D')])
            elif mode == 'Histo':
                channels_index = [self.channels_enabled[k]['index'] for k in self.channels_enabled.keys() if self.channels_enabled[k]['enabled']]
                for ind, channel in enumerate(channels_index):
                    self.controller.TH260_GetHistogram(self.device, self.data_pointers[ind], channel=channel, clear=False)

                self.data_grabed_signal.emit([OrderedDict(name='TH260', data=self.datas, type='Data1D',)])


        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [str(e), 'log']))

    def emit_data_tmp(self):
        """
        """
        try:
            print('emit temp')
            #lock = QMutexLocker(self.locker)
            mode = self.settings.child('acquisition', 'acq_type').value()
            if mode == 'Counting':
                rates = self.get_rates()
                self.data_grabed_signal_temp.emit([OrderedDict(name='TH260', data=rates[1:], type='Data0D')])
            elif mode == 'Histo':
                channels_index = [self.channels_enabled[k]['index'] for k in self.channels_enabled.keys() if self.channels_enabled[k]['enabled']]
                for ind, channel in enumerate(channels_index):
                    self.controller.TH260_GetHistogram(self.device, self.data_pointers[ind], channel=channel)

                self.data_grabed_signal_temp.emit([OrderedDict(name='TH260', data=self.datas, type='Data1D',)])

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [str(e), 'log']))

    def set_acq_mode(self, mode, update=False):
        """
        Change the acquisition mode (histogram for mode=='Counting' and 'Histo' or T3 for mode == 'FLIM')
        Parameters
        ----------
        mode

        Returns
        -------

        """
        #check enabled channels
        labels = [k for k in self.channels_enabled.keys() if self.channels_enabled[k]['enabled']]
        N = len(labels)

        if mode == 'FLIM':
            if mode != self.actual_mode or update:
                self.controller.TH260_Initialize(self.device, mode=2)  # mode T3
            self.data_grabed_signal_temp.emit([OrderedDict(name='TH260', data=[], type='DataND')])
        else:
            if mode != self.actual_mode or update:
                self.controller.TH260_Initialize(self.device, mode=0)  # histogram
            if mode == 'Counting':
                self.datas = [np.zeros((1,), dtype=np.uint32) for ind in range(N)]
                self.data_grabed_signal_temp.emit([OrderedDict(name='TH260', data=self.datas, type='Data0D', labels=labels)])
            elif mode == 'Histo':
                self.datas = [np.zeros((self.settings.child('acquisition', 'timings', 'nbins').value(),), dtype=np.uint32) for ind in range(N)]
                self.data_grabed_signal_temp.emit([OrderedDict(name='TH260', data=self.datas, type='Data1D',
                                                                x_axis=self.get_xaxis(), labels=labels)])

        self.data_pointers = [data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)) for data in self.datas]
        self.actual_mode = mode

    def ini_channels(self):
        self.controller.TH260_SetSyncDiv(self.device, self.settings.child('line_settings', 'sync_settings', 'divider').value())
        self.controller.TH260_SetSyncCFD(self.device, self.settings.child('line_settings', 'sync_settings', 'level').value(),
                                                      self.settings.child('line_settings', 'sync_settings', 'zerox').value())
        self.controller.TH260_SetSyncChannelOffset(self.device, self.settings.child('line_settings', 'sync_settings', 'offset').value())

        self.controller.TH260_SetInputCFD(self.device, 0,
                                          self.settings.child('line_settings', 'ch1_settings', 'level').value(),
                                          self.settings.child('line_settings', 'ch1_settings', 'zerox').value())
        self.controller.TH260_SetInputCFD(self.device, 1,
                                          self.settings.child('line_settings', 'ch2_settings', 'level').value(),
                                          self.settings.child('line_settings', 'ch2_settings', 'zerox').value())
        self.controller.TH260_SetInputChannelOffset(self.device, 0,
                                          self.settings.child('line_settings', 'ch1_settings', 'offset').value())
        self.controller.TH260_SetInputChannelOffset(self.device, 1,
                                                    self.settings.child('line_settings', 'ch2_settings',
                                                                        'offset').value())
        param = self.settings.child('line_settings', 'ch1_settings', 'deadtime')
        code = param.opts['limits'].index(param.value())
        self.controller.TH260_SetInputDeadTime(self.device, 0, code)
        param = self.settings.child('line_settings', 'ch2_settings', 'deadtime')
        code = param.opts['limits'].index(param.value())
        self.controller.TH260_SetInputDeadTime(self.device, 1, code)

        self.Nchannels = self.controller.TH260_GetNumOfInputChannels(self.device)
        if self.Nchannels >= 1:
            self.settings.child('line_settings', 'ch2_settings', 'enabled').setValue(False)
            self.settings.child('line_settings', 'ch2_settings').hide()
            self.controller.TH260_SetInputChannelEnable(self.device, channel=0,
                                                        enable=self.settings.child('line_settings', 'ch1_settings',
                                                                                   'enabled').value())
            self.channels_enabled['CH2']['enabled'] = False
            self.channels_enabled['CH1']['enabled'] = self.settings.child('line_settings', 'ch1_settings',
                                                                          'enabled').value()

        if self.Nchannels >= 2:
            self.settings.child('line_settings', 'ch2_settings').show()
            self.channels_enabled['CH2']['enabled'] = self.settings.child('line_settings', 'ch2_settings',
                                                                          'enabled').value()
            self.controller.TH260_SetInputChannelEnable(self.device, channel=1,
                                                        enable=self.settings.child('line_settings', 'ch2_settings',
                                                                                   'enabled').value())



    def ini_detector(self, controller=None):
        """
            See Also
            --------
            DAQ_utils.ThreadCommand, hardware1D.DAQ_1DViewer_Picoscope.update_pico_settings
        """
        self.status.update(edict(initialized=False,info="",x_axis=None,y_axis=None,controller=None))
        try:

            if self.settings.child(('controller_status')).value()=="Slave":
                if controller is None: 
                    raise Exception('no controller has been defined externally while this detector is a slave one')
                else:
                    self.controller=controller
            else:
                self.device = self.settings.child(('device')).value()
                self.settings.child(('device')).setOpts(readonly=True) #not possible to change it once initialized
                self.controller = timeharp260.Th260()

                # open device and initialize it
                self.controller.TH260_OpenDevice(self.device)

            #set timer to update info from controller
            self.general_timer = QTimer()
            self.general_timer.setInterval(200)
            self.general_timer.timeout.connect(self.update_timer)


            #set timer to check acquisition state
            self.acq_timer = QTimer()
            self.acq_timer.setInterval(500)
            self.acq_timer.timeout.connect(self.check_acquisition)

            self.set_acq_mode(self.settings.child('acquisition', 'acq_type').value(),update=True)

            model, partn, version = self.controller.TH260_GetHardwareInfo(self.device)
            serial = self.controller.TH260_GetSerialNumber(self.device)
            self.settings.child(('infos')).setValue('serial: {}, model: {}, pn: {}, version: {}'.format(serial, model, partn, version))

            self.ini_channels()

            self.set_get_resolution()

            #self.locker = QMutex()

            #self.general_timer.start(200)  # Timer event fired every 500ms

            #%%%%%%% init axes from image
            self.x_axis = self.get_xaxis()
            self.status.x_axis = self.x_axis
            self.status.initialized = True
            self.status.controller = self.controller

            return self.status

        except Exception as e:
            self.status.info = str(e)
            self.status.initialized = False
            return self.status

    def poll_acquisition(self):
        while not self.controller.TH260_CTCStatus(self.device):
            # elapsed_time = self.controller.TH260_GetElapsedMeasTime(self.device)  # in ms
            # self.settings.child('acquisition', 'elapsed_time').setValue(elapsed_time / 1000)  # in s
            QtWidgets.QApplication.processEvents()
            QThread.msleep(100)
            #self.emit_data_tmp()


        self.controller.TH260_StopMeas(self.device)
        self.emit_data()

    def check_acquisition(self):
        if not self.controller.TH260_CTCStatus(self.device):
            elapsed_time = self.controller.TH260_GetElapsedMeasTime(self.device)  # in ms
            self.settings.child('acquisition', 'elapsed_time').setValue(elapsed_time/1000)  # in s
            self.emit_data_tmp()
        else:
            self.acq_timer.stop()
            QtWidgets.QApplication.processEvents()  # this to be sure the timer is not fired while emitting data
            #self.controller.TH260_StopMeas(self.device)
            QtWidgets.QApplication.processEvents()  #this to be sure the timer is not fired while emitting data
            self.emit_data()

    def get_rates(self):
        vals = []
        sync_rate = self.controller.TH260_GetSyncRate(self.device)
        self.settings.child('acquisition', 'rates', 'syncrate').setValue(sync_rate)
        vals.append([sync_rate/1000])
        for ind_channel in range(self.Nchannels):
            if self.settings.child('line_settings',  'ch{:d}_settings'.format(ind_channel+1), 'enabled').value():
                rate = self.controller.TH260_GetCountRate(self.device, ind_channel)
                vals.append([rate/1000])
                self.settings.child('acquisition', 'rates', 'ch{:d}_rate'.format(ind_channel+1)).setValue(rate)
            else:
                vals.append([0])

        if self.settings.child('acquisition', 'rates', 'large_display').value():
            self.emit_status(ThreadCommand('lcd', [vals]))
        return vals

    def set_sync_channel(self, param):
        """
        Set the channel or sync settings (level, zerox, ...)
        Parameters
        ----------
        param: (Parameter) either ch1_settings children, ch2_settings children or sync_settings children
        """
        if param.parent().name() == 'sync_settings':
            source = 'sync'
            source_str = 'sync'
        elif param.parent().name() == 'ch1_settings':
            source = 0
            source_str = 'CH1'
        elif param.parent().name() == 'ch2_settings':
            source = 1
            source_str = 'CH2'

        if param.name() == 'divider':
            self.controller.TH260_SetSyncDiv(self.device, param.value())

        elif param.name() == 'zerox' or param.name() == 'level':
            level = param.parent().child(('level')).value()
            zerox = param.parent().child(('zerox')).value()
            if source == 'sync':
                self.controller.TH260_SetSyncCFD(self.device, level, zerox)
            else:
                self.controller.TH260_SetInputCFD(self.device, source, level, zerox)

        elif param.name() == 'offset':
            if source == 'sync':
                self.controller.TH260_SetSyncChannelOffset(self.device,param.value())
            else:
                self.controller.TH260_SetInputChannelOffset(self.device, source, param.value())

        elif param.name() == 'enabled':
            self.controller.TH260_SetInputChannelEnable(self.device, source, enable=param.value())
            self.channels_enabled[source_str]['enabled'] = param.value()
            for par in param.parent().children():
                if par != param:
                    par.setOpts(enabled=param.value())

        elif param.name() == 'deadtime':
            code = param.opts['limits'].index(param.value())
            self.controller.TH260_SetInputDeadTime(self.device, source, code)


    def set_get_resolution(self, wintype='resolution'):
        """
        Set and get right values of bin time resolution number of bins and gloabl time window
        Parameters
        ----------
        wintype: (str) either 'nbins' or 'resolution'

        Returns
        -------

        """

        base_res, max_bin_size_code = self.controller.TH260_GetBaseResolution(self.device)  # bas res in ps
        self.settings.child('acquisition', 'timings', 'base_resolution').setValue(base_res)
        resolution = self.settings.child('acquisition', 'timings', 'resolution').value()  # in ns
        Nbins = self.settings.child('acquisition', 'timings', 'nbins').value()

        bin_size_code = int(np.log(resolution * 1000 / base_res)/np.log(2))
        if bin_size_code < 0:
            bin_size_code = 0

        if wintype =='resolution':
            if bin_size_code >= max_bin_size_code:
                bin_size_code = max_bin_size_code-1 #see SetBinning documentation
            self.controller.TH260_SetBinning(self.device, bin_size_code)
            resolution = 2**bin_size_code * base_res / 1000
            resolution=self.controller.TH260_GetResolution(self.device)/1000
            self.settings.child('acquisition', 'timings', 'resolution').setValue(resolution)
        elif wintype =='nbins':
            Nbins = self.controller.TH260_SetHistoLen(self.device, int(np.log(Nbins/1024)/np.log(2)))
            self.settings.child('acquisition', 'timings', 'nbins').setValue(Nbins)

        self.settings.child('acquisition', 'timings', 'window').setValue(Nbins*resolution/1e6)  # in ms
        self.set_acq_mode(self.settings.child('acquisition', 'acq_type').value())


    def update_timer(self):
        """

        """
        self.get_rates()
        warn = self.controller.TH260_GetWarnings(self.device)
        if warn != '':
            self.emit_status(ThreadCommand('Update_Status', [warn, '']))


    def close(self):
        """

        """
        self.datas = None
        self.data_pointers = None
        self.general_timer.stop()
        QtWidgets.QApplication.processEvents()
        #QThread.msleep(1000)
        self.controller.TH260_CloseDevice(self.device)

    def get_xaxis(self):
        """
            Obtain the horizontal axis of the data.

            Returns
            -------
            1D numpy array
                Contains a vector of integer corresponding to the horizontal camera pixels.
        """
        if self.controller is not None:
            res = self.settings.child('acquisition', 'timings', 'resolution').value()
            Nbins = self.settings.child('acquisition', 'timings', 'nbins').value()
            self.x_axis = dict(data=np.linspace(0, (Nbins-1)*res/1e9, Nbins), label='Time', units='s')
        else:
            raise(Exception('Controller not defined'))
        return self.x_axis

    def get_yaxis(self):
        """
            Obtain the vertical axis of the image.

            Returns
            -------
            1D numpy array
                Contains a vector of integer corresponding to the vertical camera pixels.
        """
        if self.controller is not None:
            pass
        else: raise(Exception('Controller not defined'))
        return self.y_axis



    def grab_data(self, Naverage=1, **kwargs):
        """
            Start new acquisition in two steps :
                * Initialize data: self.datas for the memory to store new data and self.data_average to store the average data
                * Start acquisition with the given exposure in ms, in "1d" or "2d" mode

            =============== =========== =============================
            **Parameters**   **Type**    **Description**
            Naverage         int         Number of images to average
            =============== =========== =============================

            See Also
            --------
            DAQ_utils.ThreadCommand
        """
        try:
            self.acq_done = False
            mode = self.settings.child('acquisition', 'acq_type').value()
            if mode == 'Counting':
                QThread.msleep(100) #sleeps 100ms otherwise the loop is too fast
                self.emit_data()

            elif mode == 'Histo':
                time_acq = int(self.settings.child('acquisition', 'acq_time').value()*1000)  # in ms
                self.controller.TH260_ClearHistMem(self.device)
                self.controller.TH260_StartMeas(self.device, time_acq)
                #self.acq_timer.start()
                self.poll_acquisition()
            elif mode == 'FLIM':
                self.general_timer.stop()


        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [str(e), "log"]))

    def stop(self):
        """
            stop the camera's actions.
        """
        try:
            #lock = QMutexLocker(self.locker)
            self.acq_timer.stop()
            QtWidgets.QApplication.processEvents()
            self.controller.TH260_StopMeas(self.device)
            QtWidgets.QApplication.processEvents()
            self.general_timer.start()
        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [str(e), "log"]))

        return ""
