"""
requires:
fast-histogram : to process histograms in TTTR mode
"""

from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal, pyqtSlot
import os
import numpy as np
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base
from easydict import EasyDict as edict
from collections import OrderedDict

from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo, zeros_aligned, get_new_file_name, DataFromPlugins, \
    Axis
from pymodaq.daq_utils.h5modules import H5Saver

from pyqtgraph.parametertree import Parameter, ParameterTree
import pyqtgraph.parametertree.parameterTypes as pTypes
import pymodaq.daq_utils.custom_parameter_tree as customparameter

from enum import IntEnum
import ctypes
from pymodaq.daq_viewer.utility_classes import comon_parameters
from pymodaq_plugins.hardware.picoquant import timeharp260
from pymodaq.daq_utils.daq_utils import get_set_local_dir
local_path = get_set_local_dir()
import tables
try:
    from phconvert import pqreader
except:
    pass

import time
import datetime
from fast_histogram import histogram1d


class DAQ_1DViewer_TH260(DAQ_Viewer_base):
    """
        See Also
        --------
        utility_classes.DAQ_Viewer_base
    """

    params = comon_parameters+[
            {'title': 'Device index:', 'name': 'device', 'type': 'int', 'value': 0, 'max': 3, 'min': 0},
            {'title': 'Infos:', 'name': 'infos', 'type': 'str', 'value': "", 'readonly': True},
            {'title': 'Line Settings:', 'name': 'line_settings', 'type': 'group', 'expanded': False, 'children': [
                {'title': 'Sync Settings:', 'name': 'sync_settings', 'type': 'group', 'expanded': True, 'children': [
                    {'title': 'ZeroX (mV):', 'name': 'zerox', 'type': 'int', 'value': -10, 'max': 0, 'min': -40},
                    {'title': 'Level (mV):', 'name': 'level', 'type': 'int', 'value': -50, 'max': 0, 'min': -1200},
                    {'title': 'Offset (ps):', 'name': 'offset', 'type': 'int', 'value': 30000, 'max': 99999, 'min': -99999},
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
                                'value': 'Histo', 'values': ['Counting', 'Histo', 'T3']},
                 {'title': 'Base path:', 'name': 'base_path', 'type': 'browsepath', 'value': 'E:\Data',
                 'filetype': False, 'readonly': True, 'visible': False },
                 {'title': 'Temp. File:', 'name': 'temp_file', 'type': 'str', 'value': '', 'visible': False},
                 {'title': 'Acq. time (s):', 'name': 'acq_time', 'type': 'float', 'value': 1, 'min': 0.1,
                                    'max': 360000},
                 {'title': 'Elapsed time (s):', 'name': 'elapsed_time', 'type': 'float', 'value': 0, 'min': 0,
                                    'readonly': True},

                 {'title': 'Timings:', 'name': 'timings', 'type': 'group', 'expanded': True, 'children': [
                     {'title': 'Mode:', 'name': 'timing_mode', 'type': 'list', 'value': 'Hires',
                                'values': ['Hires', 'Lowres']},
                     {'title': 'Base Resolution (ps):', 'name': 'base_resolution', 'type': 'float', 'value': 25,
                                'min': 0, 'readonly': True},
                     {'title': 'Resolution (ns):', 'name': 'resolution', 'type': 'float', 'value': 0.2, 'min': 0},
                     {'title': 'Time window (s):', 'name': 'window', 'type': 'float', 'value': 100, 'min': 0,
                                    'readonly': True, 'enabled': False, 'siPrefix': True},
                     {'title': 'Nbins:', 'name': 'nbins', 'type': 'list', 'value': 1024,
                                'values': [1024*(2**lencode) for lencode in range(6)]},
                     {'title': 'Offset (ns):', 'name': 'offset', 'type': 'int', 'value': 0, 'max': 100000000, 'min': 0},
                 ]},
                {'title': 'FLIM histograms:', 'name': 'flim_histo', 'type': 'group', 'expanded': True, 'children': [
                    {'title': 'FLIM Nbins:', 'name': 'nbins_flim', 'type': 'list', 'value': 512,
                     'values': [256 * (2 ** lencode) for lencode in range(6)]},
                    {'title': 'FLIM Time Window (ns):', 'name': 'time_window_flim', 'type': 'float', 'value': 200,}
                ]},
                 {'title': 'Rates:', 'name': 'rates', 'type': 'group', 'expanded': True, 'children': [
                     {'title': 'Show large display?', 'name': 'large_display', 'type': 'bool', 'value': True},
                     {'title': 'Sync rate (cts/s):', 'name': 'syncrate', 'type': 'int', 'value': 0, 'min': 0, 'readonly': True, 'siPrefix': True},
                     {'title': 'CH1 rate (cts/s):', 'name': 'ch1_rate', 'type': 'int', 'value': 0, 'min': 0, 'readonly': True, 'siPrefix': True},
                     {'title': 'CH2 rate (cts/s):', 'name': 'ch2_rate', 'type': 'int', 'value': 0, 'min': 0, 'readonly': True, 'siPrefix': True},
                     {'title': 'Nrecords:', 'name': 'records', 'type': 'int', 'value': 0, 'min': 0, 'readonly': True,  'siPrefix': True},
                 ]},
             ]},

            ]

    hardware_averaging = False
    stop_tttr = pyqtSignal()

    def __init__(self, parent=None, params_state=None):

        super(DAQ_1DViewer_TH260, self).__init__(parent, params_state) #initialize base class with commom attributes and methods

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
        self.h5saver = None
        self.detector_thread = None
        self.time_t3 = 0
        self.time_t3_rate = 0
        self.ind_reading = 0
        self.ind_offset = 0
        self.marker_array = None
        self.nanotimes_array = None
        self.timestamp_array = None

    @classmethod
    def extract_TTTR_histo_every_pixels(cls, nanotimes, markers, marker=65, Nx=1, Ny=1, Ntime=512, time_window=None,
                                        ind_line_offset=0,
                                        channel=0):
        """
        Extract histograms from photon tags and attributes them in the given pixel of the FLIM
        The marker is used to check where a new line within the image starts
        Parameters
        ----------
        nanotimes: (ndarray of uint16) photon arrival times (in timeharp units)
        markers: (ndarray of uint8) markers: 0 means the corresponding nanotime is a photon on detector 0,
                                             1 means the corresponding nanotime is a photon on detector 1,
                                             65 => Marker 1 event
                                             66 => Marker 2 event
                                             ...
                                             79 => Marker 15 event
                                             127 =>overflow
        marker: (int) the marker value corresponding to a new Y line within the image (for instance 65)
        Nx: (int) the number of pixels along the xaxis
        Ny: (int) the number of pixels along the yaxis
        Ntime: (int) the number of pixels along the time axis
        time_window: (int) the maximum time value (in units of the TTTR resolution)
        ind_line_offset: (int) the offset of previously read lines
        channel: (int) marker of the specific channel (0 or 1) for channel 1 or 2

        Returns
        -------
        ndarray: FLIM hypertemporal image in the order (X, Y, time)
        """

        if time_window is None:
            time_window = Ntime
        ind_lines = np.where(markers == marker)[0]

        # nanotimes = nanotimes[np.logical_or(markers == marker, markers == channel)]
        # markers = markers[np.logical_or(markers == marker, markers == channel)]
        # indexes_new_line = np.squeeze(np.argwhere(markers == marker)).astype(np.uint64)

        if ind_lines.size == 0:
            ind_lines = np.array([0, nanotimes.size], dtype=np.uint64)
        # print(indexes_new_line)
        datas = np.zeros((Nx, Ny, Ntime))
        for ind_line in range(ind_lines.size - 1):
            # print(ind_line)
            ix = ((ind_line + ind_line_offset) // Ny) % Nx
            iy = (ind_line + ind_line_offset) % Ny
            is_nanotime = markers[ind_lines[ind_line]:ind_lines[ind_line + 1]] == channel
            datas[ix, iy, :] += histogram1d(nanotimes[ind_lines[ind_line]:ind_lines[ind_line+1]][is_nanotime], Ntime,
                                            (0, int(time_window)-1))

        return datas

    def emit_log(self, string):
        self.emit_status(ThreadCommand('Update_Status', [string, 'log']))

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
                self.set_get_resolution(wintype='both')
                if param.value() == 'Counting' or param.value() == 'Histo':
                    self.settings.child('acquisition', 'temp_file').hide()
                    self.settings.child('acquisition', 'base_path').hide()

                else:
                    self.settings.child('acquisition', 'temp_file').show()
                    self.settings.child('acquisition', 'base_path').show()


                #     self.settings.child('acquisition', 'timings', 'nbins').setOpts(
                #         limits=[128 * (2 ** lencode) for lencode in range(6)])
                #     self.settings.child('acquisition', 'timings', 'nbins').setValue(128)
                #
                # else:
                #     self.settings.child('acquisition', 'timings', 'nbins').setOpts(
                #         limits=[1024 * (2 ** lencode) for lencode in range(6)])
                #     self.settings.child('acquisition', 'timings', 'nbins').setValue(1024)

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
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))


    def emit_data(self):
        """
        """
        try:
            mode = self.settings.child('acquisition', 'acq_type').value()
            if mode == 'Counting':
                rates = [np.array(rate) for rate in self.get_rates()[1:]]
                self.data_grabed_signal.emit([DataFromPlugins(name='TH260', data=rates, dim='Data0D')])
            elif mode == 'Histo':
                channels_index = [self.channels_enabled[k]['index'] for k in self.channels_enabled.keys() if self.channels_enabled[k]['enabled']]
                for ind, channel in enumerate(channels_index):
                    self.controller.TH260_GetHistogram(self.device, self.data_pointers[ind], channel=channel, clear=True)
                records = np.sum(np.array([np.sum(data) for data in self.datas]))
                self.settings.child('acquisition', 'rates', 'records').setValue(records)
                self.data_grabed_signal.emit([DataFromPlugins(name='TH260', data=self.datas, dim='Data1D',)])
                self.general_timer.start()

            elif mode == 'T3':
                self.h5saver.h5_file.flush()
                self.data_grabed_signal.emit([DataFromPlugins(name='TH260', data=[self.datas], dim='Data1D',
                                                          external_h5=self.h5saver.h5_file)])
                self.general_timer.start()




        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo()+ str(e), 'log']))

    def emit_data_tmp(self):
        """
        """
        try:
            mode = self.settings.child('acquisition', 'acq_type').value()
            if mode == 'Counting':
                rates = [np.array(rate) for rate in self.get_rates()[1:]]
                self.data_grabed_signal_temp.emit([DataFromPlugins(name='TH260', data=rates, dim='Data0D')])
            elif mode == 'Histo':
                channels_index = [self.channels_enabled[k]['index'] for k in self.channels_enabled.keys() if self.channels_enabled[k]['enabled']]
                for ind, channel in enumerate(channels_index):
                    self.controller.TH260_GetHistogram(self.device, self.data_pointers[ind], channel=channel, clear=False)
                records = np.sum(np.array([np.sum(data) for data in self.datas]))
                self.settings.child('acquisition', 'rates', 'records').setValue(records)
                self.data_grabed_signal_temp.emit([DataFromPlugins(name='TH260', data=self.datas, dim='Data1D',)])
            elif mode == 'T3':
                self.data_grabed_signal_temp.emit([DataFromPlugins(name='TH260', data=[self.datas], dim='Data1D')])


        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo()+ str(e), 'log']))

    def process_histo_from_h5(self, Nx=1, Ny=1, channel=0, marker=65):
        markers_array = self.h5saver.h5_file.get_node('/markers')
        nanotimes_array = self.h5saver.h5_file.get_node('/nanotimes')

        Nbins = self.settings.child('acquisition', 'timings', 'nbins').value()
        time_window = Nbins

        ind_lines = np.where(markers_array[self.ind_reading:] == marker)[0]
        if len(ind_lines) > 2:
            ind_last_line = ind_lines[-1]
            markers_tmp = markers_array[self.ind_reading:self.ind_reading + ind_last_line]
            nanotimes_tmp = nanotimes_array[self.ind_reading:self.ind_reading + ind_last_line]

            datas = self.extract_TTTR_histo_every_pixels(nanotimes_tmp, markers_tmp, marker=marker, Nx=Nx, Ny=Ny,
                                Ntime=Nbins, ind_line_offset=self.ind_offset, channel=channel, time_window=time_window)
            self.ind_reading += ind_lines[-2]
            self.ind_offset += len(ind_lines)-2
        return datas

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

        if mode != self.actual_mode or update:

            if mode == 'Counting':
                self.controller.TH260_Initialize(self.device, mode=0)  # histogram
                self.datas = [np.zeros((1,), dtype=np.uint32) for ind in range(N)]
                self.data_grabed_signal_temp.emit([DataFromPlugins(name='TH260', data=self.datas, dim='Data0D', labels=labels)])
                self.data_pointers = [data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)) for data in self.datas]
            elif mode == 'Histo':
                self.controller.TH260_Initialize(self.device, mode=0)  # histogram
                self.datas = [np.zeros((self.settings.child('acquisition', 'timings', 'nbins').value(),), dtype=np.uint32) for ind in range(N)]
                self.data_grabed_signal_temp.emit([DataFromPlugins(name='TH260', data=self.datas, dim='Data1D',
                                                                x_axis=self.get_xaxis(), labels=labels)])
                self.data_pointers = [data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)) for data in self.datas]
            elif mode == 'T3':
                self.controller.TH260_Initialize(self.device, mode=3)  # T3 mode
                self.datas = [np.zeros((self.settings.child('acquisition', 'timings', 'nbins').value(),), dtype=np.uint32) for ind in range(N)]
                self.data_grabed_signal_temp.emit([DataFromPlugins(name='TH260', data=self.datas, dim='Data1D',
                                                                x_axis=self.get_xaxis(), labels=labels)])
                self.data_pointers = [data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)) for data in self.datas]

            self.actual_mode = mode

    def ini_channels(self):
        self.controller.TH260_SetSyncDiv(self.device,
                                         self.settings.child('line_settings', 'sync_settings', 'divider').value())

        self.controller.TH260_SetSyncCFD(self.device,
                                         self.settings.child('line_settings', 'sync_settings', 'level').value(),
                                         self.settings.child('line_settings', 'sync_settings', 'zerox').value())

        self.controller.TH260_SetSyncChannelOffset(self.device, self.settings.child('line_settings', 'sync_settings',
                                                                                    'offset').value())

        self.controller.TH260_SetInputCFD(self.device, 0,
                                          self.settings.child('line_settings', 'ch1_settings', 'level').value(),
                                          self.settings.child('line_settings', 'ch1_settings', 'zerox').value())
        self.controller.TH260_SetInputCFD(self.device, 1,
                                          self.settings.child('line_settings', 'ch2_settings', 'level').value(),
                                          self.settings.child('line_settings', 'ch2_settings', 'zerox').value())

        self.controller.TH260_SetInputChannelOffset(self.device, 0,
                                          self.settings.child('line_settings', 'ch1_settings', 'offset').value())
        self.controller.TH260_SetInputChannelOffset(self.device, 1,
                                          self.settings.child('line_settings', 'ch2_settings', 'offset').value())

        param = self.settings.child('line_settings', 'ch1_settings', 'deadtime')
        code = param.opts['limits'].index(param.value())
        self.controller.TH260_SetInputDeadTime(self.device, 0, code)
        param = self.settings.child('line_settings', 'ch2_settings', 'deadtime')
        code = param.opts['limits'].index(param.value())
        self.controller.TH260_SetInputDeadTime(self.device, 1, code)

        self.Nchannels = self.controller.TH260_GetNumOfInputChannels(self.device)
        if self.Nchannels >= 1:
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

            #init the device and memory in the selected mode
            self.set_acq_mode(self.settings.child('acquisition', 'acq_type').value(), update=True)

            model, partn, version = self.controller.TH260_GetHardwareInfo(self.device)
            serial = self.controller.TH260_GetSerialNumber(self.device)
            self.settings.child(('infos')).setValue('serial: {}, model: {}, pn: {}, version: {}'.format(serial, model, partn, version))

            self.ini_channels()

            self.set_get_resolution(wintype='both')

            self.emit_status(ThreadCommand('init_lcd', [dict(labels=['CH1 rate (kcts/s)', 'CH2 Rate (kcts/s)'], Nvals=2,
                                                             digits=6)]))

            self.general_timer.start()  # Timer event fired every 200ms

            #%%%%%%% init axes from image
            self.x_axis = self.get_xaxis()
            self.status.x_axis = self.x_axis
            self.status.initialized = True
            self.status.controller = self.controller

            return self.status

        except Exception as e:
            self.status.info = getLineInfo()+ str(e)
            self.status.initialized = False
            return self.status

    def poll_acquisition(self):
        """
        valid only for histogramming mode
        Returns
        -------

        """
        while not self.controller.TH260_CTCStatus(self.device):
            # elapsed_time = self.controller.TH260_GetElapsedMeasTime(self.device)  # in ms
            # self.settings.child('acquisition', 'elapsed_time').setValue(elapsed_time / 1000)  # in s
            QtWidgets.QApplication.processEvents()
            QThread.msleep(100)
            #self.emit_data_tmp()

        self.controller.TH260_StopMeas(self.device)
        self.emit_data()

    @pyqtSlot(int)
    def set_elapsed_time(self, elapsed_time):
        self.settings.child('acquisition', 'elapsed_time').setValue(elapsed_time/1000)  # in s

    def check_acquisition(self):
        if not self.controller.TH260_CTCStatus(self.device):
            elapsed_time = self.controller.TH260_GetElapsedMeasTime(self.device)  # in ms
            self.set_elapsed_time(elapsed_time)
            self.emit_data_tmp()
        else:
            self.acq_timer.stop()
            QtWidgets.QApplication.processEvents()  # this to be sure the timer is not fired while emitting data
            self.controller.TH260_StopMeas(self.device)
            QtWidgets.QApplication.processEvents()  #this to be sure the timer is not fired while emitting data
            self.emit_data()

    def get_rates(self):
        vals = []
        sync_rate = self.controller.TH260_GetSyncRate(self.device)

        vals.append([sync_rate/1000])
        for ind_channel in range(self.Nchannels):
            if self.settings.child('line_settings',  'ch{:d}_settings'.format(ind_channel+1), 'enabled').value():
                rate = self.controller.TH260_GetCountRate(self.device, ind_channel)
                vals.append([rate/1000])
            else:
                vals.append([0])

        self.emit_rates(vals)
        return vals

    def emit_rates(self,vals):
        self.settings.child('acquisition', 'rates', 'syncrate').setValue(vals[0][0]*1000)
        for ind_channel in range(self.Nchannels):
            self.settings.child('acquisition', 'rates', 'ch{:d}_rate'.format(ind_channel+1)).setValue(vals[ind_channel+1][0]*1000)

        if self.settings.child('acquisition', 'rates', 'large_display').value():
            self.emit_status(ThreadCommand('lcd', [vals[1:]]))
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
        wintype: (str) either 'nbins' or 'resolution' or 'both'

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

        if wintype =='resolution' or wintype =='both':
            if bin_size_code >= max_bin_size_code:
                bin_size_code = max_bin_size_code-1 #see SetBinning documentation
            self.controller.TH260_SetBinning(self.device, bin_size_code)
            resolution = 2**bin_size_code * base_res / 1000
            resolution=self.controller.TH260_GetResolution(self.device)/1000
            self.settings.child('acquisition', 'timings', 'resolution').setValue(resolution)
        if wintype =='nbins' or wintype =='both':
            mode = self.settings.child('acquisition', 'acq_type').value()

            if mode == 'Counting' or mode == 'Histo':
                Nbins = self.controller.TH260_SetHistoLen(self.device, int(np.log(Nbins/1024)/np.log(2)))
            self.settings.child('acquisition', 'timings', 'nbins').setValue(Nbins)

            N = len([k for k in self.channels_enabled.keys() if self.channels_enabled[k]['enabled']])
            if mode == 'Counting':
                self.datas = [np.zeros((1,), dtype=np.uint32) for ind in range(N)]
            elif mode == 'Histo' or mode == 'T3':
                self.datas = [np.zeros((Nbins,), dtype=np.uint32) for ind in range(N)]
                self.get_xaxis()
                self.emit_x_axis()
            self.data_pointers = [data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)) for data in self.datas]


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
        self.stop()
        QtWidgets.QApplication.processEvents()
        self.datas = None
        self.data_pointers = None
        self.general_timer.stop()
        QtWidgets.QApplication.processEvents()
        #QThread.msleep(1000)
        self.controller.TH260_CloseDevice(self.device)
        if self.h5saver is not None:
            if self.h5saver.h5_file is not None:
                if self.self.h5saver.h5_file.isopen:
                    self.self.h5saver.h5_file.flush()
                    self.self.h5saver.h5_file.close()

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
            self.x_axis = Axis(data=np.linspace(0, (Nbins-1)*res, Nbins), label='Time', units='ns')
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
                self.acq_timer.start()
                #self.poll_acquisition()

            elif mode == 'T3':
                self.ind_reading = 0
                self.ind_offset = 0
                self.Nx = 1
                self.Ny = 1
                self.init_h5file()
                self.datas = np.zeros((self.settings.child('acquisition', 'timings', 'nbins').value(),), dtype=np.float64)


                time_acq = int(self.settings.child('acquisition', 'acq_time').value() * 1000)  # in ms
                self.general_timer.stop()

                t3_reader = T3Reader(self.device, self.controller, time_acq, self.Nchannels)
                self.detector_thread = QThread()
                t3_reader.moveToThread(self.detector_thread)

                t3_reader.data_signal[dict].connect(self.populate_h5)
                self.stop_tttr.connect(t3_reader.stop_TTTR)

                self.detector_thread.t3_reader = t3_reader
                self.detector_thread.start()
                self.detector_thread.setPriority(QThread.HighestPriority)
                self.time_t3 = time.perf_counter()
                self.time_t3_rate = time.perf_counter()
                t3_reader.start_TTTR()


        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), "log"]))


    def init_h5file(self):

        file, curr_dir = get_new_file_name(self.settings.child('acquisition','base_path').value(), 'tttr_data')

        self.h5saver = H5Saver(save_type='custom')
        self.h5saver.init_file(update_h5=False, custom_naming=True,
                               addhoc_file_path=os.path.join(curr_dir, f'{file}.h5'),
                               metadata=dict(settings=customparameter.parameter_to_xml_string(self.settings),
                                             format_name='timestamps'))
        self.settings.child('acquisition', 'temp_file').setValue(f'{file}.h5')
        self.marker_array = self.h5saver.add_array(self.h5saver.raw_group, 'markers', 'data', data_dimension='1D',
                                                   array_type=np.int, enlargeable=True)
        self.nanotimes_array = self.h5saver.add_array(self.h5saver.raw_group, 'nanotimes', 'data', data_dimension='1D',
                                                      array_type=np.int, enlargeable=True)
        self.timestamp_array = self.h5saver.add_array(self.h5saver.raw_group, 'nanotimes', 'data', data_dimension='1D',
                                                      array_type=np.int, enlargeable=True)

        # #self.h5file = tables.open_file(os.path.join(curr_dir, file+'.h5'), mode='w')
        # h5group = self.h5file.root
        # h5group._v_attrs['settings'] = customparameter.parameter_to_xml_string(self.settings)
        # h5group._v_attrs.type = 'detector'
        # h5group._v_attrs['format_name'] = 'timestamps'
        #
        # channels_index = [self.channels_enabled[k]['index'] for k in self.channels_enabled.keys() if
        #                   self.channels_enabled[k]['enabled']]
        # self.marker_array = self.h5file.create_earray(self.h5file.root, 'markers', tables.UInt8Atom(), (0,),
        #                                               title='markers')
        # self.marker_array._v_attrs['data_type'] = '1D'
        # self.marker_array._v_attrs['type'] = 'tttr_data'
        #
        # self.nanotimes_array = self.h5file.create_earray(self.h5file.root, 'nanotimes', tables.UInt16Atom(), (0,),
        #                                                  title='nanotimes')
        # self.nanotimes_array._v_attrs['data_type'] = '1D'
        # self.nanotimes_array._v_attrs['type'] = 'tttr_data'
        #
        # self.timestamp_array = self.h5file.create_earray(self.h5file.root, 'timestamps', tables.UInt64Atom(), (0,),
        #                                            title='timestamps')
        # self.timestamp_array._v_attrs['data_type'] = '1D'
        # self.timestamp_array._v_attrs['type'] = 'tttr_data'
        #
        # # self.raw_datas_array = self.h5file.create_earray(self.h5file.root, 'raw_data', tables.UInt64Atom(), (0,),
        # #                                           title='raw_data')
        # # self.raw_datas_array._v_attrs['data_type'] = '1D'
        # # self.raw_datas_array._v_attrs['type'] = 'tttr_data'



    @pyqtSlot(dict)
    def populate_h5(self, datas):
        """

        Parameters
        ----------
        datas: (dict) dict(data=self.buffer[0:nrecords], rates=rates, elapsed_time=elapsed_time)

        Returns
        -------

        """
        if datas['data'] != []:
            # self.raw_datas_array.append(datas['data'])
            # self.raw_datas_array._v_attrs['shape'] = self.raw_datas_array.shape
            detectors, timestamps, nanotimes = pqreader.process_t3records(
                datas['data'], time_bit=10, dtime_bit=15, ch_bit=6, special_bit=True,
                ovcfunc=pqreader._correct_overflow_nsync)

            self.timestamp_array.append(timestamps)
            self.timestamp_array._v_attrs['shape'] = self.timestamp_array.shape
            self.nanotimes_array.append(nanotimes)
            self.nanotimes_array._v_attrs['shape'] = self.nanotimes_array.shape
            self.marker_array.append(detectors)
            self.marker_array._v_attrs['shape'] = self.marker_array.shape
            self.h5saver.h5_file.flush()

        if time.perf_counter() - self.time_t3_rate > 0.5:
            self.emit_rates(datas['rates'])
            self.set_elapsed_time(datas['elapsed_time'])
            self.settings.child('acquisition', 'rates', 'records').setValue(self.nanotimes_array.shape[0])
            self.time_t3_rate = time.perf_counter()

        elif time.perf_counter() - self.time_t3 > 5:
            self.datas += np.squeeze(self.process_histo_from_h5(Nx=self.Nx, Ny=self.Ny))
            self.emit_data_tmp()
            self.time_t3 = time.perf_counter()

        if datas['acquisition_done']:
            self.datas += np.squeeze(self.process_histo_from_h5(Nx=self.Nx, Ny=self.Ny))
            self.emit_data()





    def stop(self):
        """
            stop the camera's actions.
        """
        try:
            self.acq_timer.stop()
            QtWidgets.QApplication.processEvents()
            self.controller.TH260_StopMeas(self.device)
            QtWidgets.QApplication.processEvents()
            self.general_timer.start()
        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo()+ str(e), "log"]))

        return ""


class T3Reader(QObject):
    data_signal = pyqtSignal(dict)  # dict(data=self.buffer[0:nrecords], rates=rates, elapsed_time=elapsed_time)

    def __init__(self, device, controller, time_acq, Nchannels=2):
        super(T3Reader, self).__init__()

        self.Nchannels = Nchannels
        self.device = device
        self.controller = controller
        self.time_acq = time_acq
        self.acquisition_stoped = False
        self.buffer = zeros_aligned(2 ** 14, 4096, dtype=np.uint32)
        self.data_ptr = self.buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32))

    def set_acquisition_stoped(self):
        self.acquisition_stoped = True

    def start_TTTR(self):

        self.controller.TH260_StartMeas(self.device, self.time_acq)

        while not self.acquisition_stoped:
            if 'FIFOFULL' in self.controller.TH260_GetFlags(self.device):
                print("\nFiFo Overrun!")
                #self.stop_TTTR()

            rates = self.get_rates()
            elapsed_time = self.controller.TH260_GetElapsedMeasTime(self.device)  # in ms

            nrecords = self.controller.TH260_ReadFiFo(self.device, self.buffer.size, self.data_ptr)

            if nrecords > 0:
                # We could just iterate through our buffer with a for loop, however,
                # this is slow and might cause a FIFO overrun. So instead, we shrinken
                # the buffer to its appropriate length with array slicing, which gives
                # us a python list. This list then needs to be converted back into
                # a ctype array which can be written at once to the output file
                self.data_signal.emit(dict(data=self.buffer[0:nrecords], rates=rates, elapsed_time=elapsed_time, acquisition_done=False))
            else:

                if self.controller.TH260_CTCStatus(self.device):
                    print("\nDone")
                    self.stop_TTTR()
                    self.data_signal.emit(dict(data=[], rates=rates, elapsed_time=elapsed_time, acquisition_done=True))
            # within this loop you can also read the count rates if needed.

    def stop_TTTR(self):
        self.acquisition_stoped = True
        self.controller.TH260_StopMeas(self.device)


    def get_rates(self):
        vals = []
        sync_rate = self.controller.TH260_GetSyncRate(self.device)
        vals.append([sync_rate/1000])
        for ind_channel in range(self.Nchannels):
            rate = self.controller.TH260_GetCountRate(self.device, ind_channel)
            vals.append([rate/1000])
        return vals

