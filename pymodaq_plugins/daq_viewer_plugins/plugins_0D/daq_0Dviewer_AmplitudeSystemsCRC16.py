# -*- coding: utf-8 -*-
"""
Created on Thu Jun 14 15:14:54 2018

@author: Weber Sébastien
@email: seba.weber@gmail.com
"""
from PyQt5.QtCore import pyqtSignal, QTimer, QThread
from easydict import EasyDict as edict
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo, DataFromPlugins, set_logger, get_module_name
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base, comon_parameters
import numpy as np
from pymodaq_plugins.hardware.amplitude.amplitude_systems import AmplitudeSystemsCRC16

logger = set_logger(get_module_name(__file__))
#%%

class DAQ_0DViewer_AmplitudeSystemsCRC16(DAQ_Viewer_base):
    """
    diagnostics = [
        dict(id=0, name='Frequency PP', read_command=0x30, write_command=0x30, reply=4, unit='kHz',
             divider=1000, readonly=False, value=-1),
    """
    data_grabed_signal = pyqtSignal(list)

    params = comon_parameters+[
                {'title': 'COM port:','name': 'com_port', 'type': 'list',
                 'values': AmplitudeSystemsCRC16.get_ressources()},
                {'title': 'Timeout:', 'name': 'timeout', 'type': 'int', 'value': -1},
                {'title': 'Serial number:', 'name': 'serial_number', 'type': 'int', 'value': 0},
                {'title': 'Version:', 'name': 'version', 'type': 'str', 'value': ''},

                {'title': 'Update all Diags', 'name': 'update_diags', 'type': 'bool_push'},

                {'title': 'Startup:', 'name': 'startup', 'type': 'group', 'children': [
                    {'title': 'Laser:', 'name': 'laser', 'type': 'bool_push', 'value': False},
                    {'title': 'Shutter:', 'name': 'shutter', 'type': 'bool_push', 'value': False},
                ]},
                {'title': 'Channels:', 'name': 'channels', 'type': 'itemselect', 'height': 150,
                 'value': dict(all_items=[diag['name'] for diag in AmplitudeSystemsCRC16.diagnostics], selected=[])},

                {'title': 'Status:', 'name': 'status', 'type': 'group', 'children':
                    [{'title': stat['name'], 'name': f'stat_{stat["id"]}', 'type': 'led', 'value':bool(stat['value']),
                      'readonly': True}
                     for stat in AmplitudeSystemsCRC16.status]},
                {'title': 'Diagnostics:', 'name': 'diagnostics', 'type': 'group', 'children':
                    [{'title': f'{diag["name"]} ({diag["unit"]})', 'name': f'diag_{diag["id"]}', 'type': 'float',
                      'value':diag['value'], 'readonly': diag['readonly']}
                     for diag in AmplitudeSystemsCRC16.diagnostics]}
                ]

    def __init__(self,parent=None,params_state=None):
        super().__init__(parent, params_state)
        self.controller = None


    def ini_detector(self, controller=None):
        """
            Initialisation procedure of the detector.

            Returns
            -------

                The initialized status.

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
                    self.controller = controller
            else:
                self.controller = AmplitudeSystemsCRC16()
                self.controller.init_communication(self.settings.child(('com_port')).value())
            self.settings.child(('timeout')).setValue(self.controller.timeout)

            try:
                self.settings.child(('serial_number')).setValue(self.controller.get_sn())
                QThread.msleep(200)
            except Exception as e:
                logger.exception(str(e))
            try:
                self.settings.child(('version')).setValue(self.controller.get_version())
                QThread.msleep(200)
            except Exception as e:
                logger.exception(str(e))

            self.update_status()
            for stat in self.controller.status:
                self.settings.child('status', f'stat_{stat["id"]}').setValue(stat['value'])

            self.update_all_diags()

            self.status_timer = QTimer()
            self.status_timer.timeout.connect(self.update_status)
            self.status_timer.start(1000)

            self.status.controller = self.controller
            self.status.initialized = True
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))
            self.status.info = getLineInfo() + str(e)
            self.status.initialized = False
            return self.status

    def update_status(self):
        """
        get a list of changed status dict on the form
        dict(id=0, name='Temp Amp', value=0, byte=0, bit=0x00)
        """
        try:
            for stat in self.controller.get_status():
                self.settings.child('status', f'stat_{stat["id"]}').setValue(bool(stat['value']))
            self.settings.child('startup', 'laser').setValue(self.controller.get_laser())
            self.settings.child('startup', 'shutter').setValue(self.controller.get_shutter())
        except Exception as e:
            logger.exception(str(e))
    def update_all_diags(self):
        for diag in self.controller.diagnostics:
            try:
                QThread.msleep(200)
                self.update_diag(diag['id'])

            except Exception as e:
                print(e)


    def update_diag(self, id):
        data, diag = self.controller.get_diag_from_id(id)
        self.settings.child('diagnostics', f'diag_{id}').setValue(diag['value'] / diag['divider'])


    def reset(self):
        self.controller.flush()

    def grab_data(self, Naverage=1, **kwargs):
        """
        """
        self.status_timer.stop()
        data_tot = []
        selected_channels = self.settings.child(('channels')).value()['selected']
        for channel in selected_channels:
            data, diag = self.controller.get_diag_from_name(channel)
            data = int.from_bytes(data, 'big') / diag['divider']
            self.settings.child('diagnostics', f'diag_{diag["id"]}').setValue(data)
            data_tot.append(np.array([data]))
            QThread.msleep(200)

        self.data_grabed_signal.emit(
                [DataFromPlugins(name='AmplitudeSystems', data=data_tot, dim='Data0D', labels=selected_channels)])

        self.status_timer.start(1000)
    def stop(self):
        pass

    def commit_settings(self, param):
        """
            Activate the parameters changes in the hardware.

            =============== ================================= ============================
            **Parameters**   **Type**                         **Description**
            *param*         instance of pyqtgraph.parameter   The parameter to be checked.
            =============== ================================= ============================

            See Also
            --------
            daq_utils.ThreadCommand
        """
        try:
            self.status_timer.stop()
            if 'diag_' in param.name():
                id = int(param.name().split('diag_')[1])
                diag = self.controller.get_diag_from_id(id)
                self.controller.set_diag(id, int(param.value() * diag['divider']).to_bytes(diag['reply'], 'big'))
                QThread.msleep(200)
                self.update_diag(id)
            elif param.name() == 'timeout':
                self.controller.timeout = param.value()
                param.setValue(self.controller.timeout)
            elif param.name() == 'update_diags':
                self.update_all_diags()
                self.update_status()
            elif param.name() == 'laser':
                self.controller.set_laser(param.value())
            elif param.name() == 'shutter':
                self.controller.set_shutter(param.value())
            self.status_timer.start(1000)

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))


    def close(self):
        """
            close the current instance of the visa session.
        """
        self.status_timer.stop()
        QThread.msleep(1000)
        self.controller.close_communication()


