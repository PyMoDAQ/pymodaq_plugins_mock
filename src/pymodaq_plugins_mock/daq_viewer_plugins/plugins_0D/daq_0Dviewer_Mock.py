from qtpy import QtWidgets, QtCore

from pymodaq_utils.utils import ThreadCommand, getLineInfo
from pymodaq.utils.data import DataFromPlugins, DataToExport
import numpy as np
from pymodaq_gui.parameter.pymodaq_ptypes import GroupParameter, registerParameterType
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pyqtgraph.parametertree.parameterTypes.basetypes import GroupParameter

from pymodaq_utils.math_utils import gauss1D


MOCK_PARAMS = [
    {'title': 'Npts', 'name': 'Npts', 'type': 'int', 'value': 200, 'default': 200, 'min': 10},
    {'title': 'Amp', 'name': 'Amp', 'type': 'int', 'value': 20, 'default': 20, 'min': 1},
    {'title': 'x0', 'name': 'x0', 'type': 'float', 'value': 50, 'default': 50, 'min': 0},
    {'title': 'dx', 'name': 'dx', 'type': 'float', 'value': 20, 'default': 20, 'min': 1},
    {'title': 'n', 'name': 'n', 'type': 'int', 'value': 1, 'default': 1, 'min': 1},
    {'title': 'amp_noise', 'name': 'amp_noise', 'type': 'float', 'value': 0.1, 'default': 0.1, 'min': 0},
]


class MockScalableGroup(GroupParameter):
    def __init__(self, **opts):
        opts['addText'] = 'Add Mock'
        super().__init__(**opts)

    def addNew(self):
        indexes = [int(child.name().split('_')[1]) for child in self.children()
                   if child.name().startswith('Mock_')]
        new_index = max(indexes) + 1 if indexes else 0
        npts = next(p['value'] for p in MOCK_PARAMS if p['name'] == 'Npts')
        children = [{**p} for p in MOCK_PARAMS]
        for p in children:
            if p['name'] == 'Amp':
                p['value'] = int(np.random.randint(1, 30))
            elif p['name'] == 'x0':
                p['value'] = float(np.random.uniform(0, npts - 1))
            elif p['name'] == 'dx':
                p['value'] = float(np.random.uniform(5, npts / 3))
        self.addChild({
            'title': f'Mock {new_index:02d}',
            'name': f'Mock_{new_index:02d}',
            'type': 'bool',
            'value': True,
            'removable': True,
            'renamable': False,
            'children': children,
        })


# Need to register a new type to properly trigger addNew
registerParameterType('groupmock', MockScalableGroup, override=True)

class DAQ_0DViewer_Mock(DAQ_Viewer_base):
    params = comon_parameters + [
        {'title': 'Wait time (ms)', 'name': 'wait_time', 'type': 'int', 'value': 100, 'default': 100, 'min': 0},
        {'title': 'Separated viewers', 'name': 'sep_viewers', 'type': 'bool', 'value': False},
        {'title': 'Mock channels', 'name': 'lcd', 'type': 'group', 'children': [
            {'title': 'Show in LCD', 'name': 'show_lcd', 'type': 'bool', 'value': False},
            {'title': 'Show LCD Graph', 'name': 'lcd_graph', 'type': 'bool', 'value': False},
        ]},
        {'title':'Mock channels', 'name': 'mocks', 'type':'groupmock', 'children':[
            {'title': 'Mock 00', 'name': 'Mock_00', 'type': 'bool', 'value': True,
             'removable': True, 'renamable': False,
             'children': MOCK_PARAMS},
            {'title': 'Mock 01', 'name': 'Mock_01', 'type': 'bool', 'value': True,
             'removable': True, 'renamable': False,
             'children': [
                 {'title': 'Npts', 'name': 'Npts', 'type': 'int', 'value': 200, 'default': 200, 'min': 10},
                 {'title': 'Amp', 'name': 'Amp', 'type': 'int', 'value': 10, 'default': 10, 'min': 1},
                 {'title': 'x0', 'name': 'x0', 'type': 'float', 'value': 100, 'default': 100, 'min': 0},
                 {'title': 'dx', 'name': 'dx', 'type': 'float', 'value': 30, 'default': 30, 'min': 1},
                 {'title': 'n', 'name': 'n', 'type': 'int', 'value': 2, 'default': 2, 'min': 1},
                 {'title': 'amp_noise', 'name': 'amp_noise', 'type': 'float', 'value': 0.1, 'default': 0.1, 'min': 0},
             ]},
        ]
        },
    ]

    def ini_attributes(self):
        self.controller: str = None
        self.x_axis = None
        self.ind_data = 0
        self.lcd_init = False

    def commit_settings(self, param):
        """
            Setting the mock data.

            ============== ========= =================
            **Parameters**  **Type**  **Description**
            *param*         none      not used
            ============== ========= =================

            See Also
            --------
            set_Mock_data
        """
        self.set_Mock_data()
        if param.name() == 'wait_time':
            self.emit_status(ThreadCommand('update_main_settings', [['wait_time'], param.value(), 'value']))

    def set_Mock_data(self):
        """
            For each enabled Mock channel in the scalable group, compute a gaussian
            distribution and store it in data_mock.
        """
        self.data_mock = []
        for mock_param in self.settings.child('mocks').children():
            x = np.linspace(0, mock_param['Npts'] - 1, mock_param['Npts'])
            self.data_mock.append(
                mock_param['Amp'] * gauss1D(x, mock_param['x0'], mock_param['dx'], mock_param['n'])
                + mock_param['amp_noise'] * np.random.rand(mock_param['Npts']))

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by controller
            (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """
        self.emit_status(ThreadCommand('show_splash', 'Starting initialization'))
        QtCore.QThread.msleep(500)
        self.ini_detector_init(old_controller=controller,
                               new_controller='Mock controller')

        self.emit_status(ThreadCommand('show_splash', 'generating Mock Data'))
        QtCore.QThread.msleep(500)
        self.set_Mock_data()
        self.emit_status(ThreadCommand('update_main_settings', [['wait_time'],
                                                                self.settings.child('wait_time').value(), 'value']))
        self.emit_status(ThreadCommand('show_splash', 'Displaying initial data'))
        QtCore.QThread.msleep(500)

        enabled = [p.name() for p in self.settings.child('mocks').children() if p.value()]
        if enabled:
            self.dte_signal_temp.emit(DataToExport('Mock0D', data=[
                DataFromPlugins(name='Mock0D', data=[np.array([0.])] * len(enabled),
                                dim='Data0D', labels=enabled)]))
        self.emit_status(ThreadCommand('close_splash'))
        initialized = True
        info = 'RAS'
        return info, initialized

    def close(self):
        """
            not implemented.
        """
        pass

    def grab_data(self, Naverage=1, **kwargs):
        """
            | Start new acquisition.

            For each Mock channel in the scalable group:
                * shift right data of ind_data positions
                * if the channel is enabled, append the (averaged) scalar to data_tot

            | Send the data_grabed_signal once done.

            =============== ======== ===============================================
            **Parameters**  **Type**  **Description**
            *Naverage*      int       specify the threshold of the mean calculation
            =============== ======== ===============================================

        """
        data_tot = []
        labels = []

        for mock_param, data in zip(self.settings.child('mocks').children(), self.data_mock):
            if mock_param.value():
                data = np.roll(data, self.ind_data)
                if Naverage > 1:
                    data_tot.append(np.array([np.mean(data[0:Naverage - 1])]))
                else:
                    data_tot.append(np.array([data[0]]))
                labels.append(mock_param.name())

        if not data_tot:
            return

        if self.settings.child('sep_viewers').value():
            self.dte_signal.emit(DataToExport('Mock0D',
                                              data=[DataFromPlugins(name=label, data=[data], dim='Data0D',
                                                                    labels=[label])
                                                    for label, data in zip(labels, data_tot)]))
        else:
            self.dte_signal.emit(DataToExport('Mock0D',
                                              data=[DataFromPlugins(name='Mock0D', data=data_tot,
                                                                    dim='Data0D', labels=labels)]))
        self.ind_data += 1
        if self.settings['lcd', 'show_lcd']:
            if not self.lcd_init:
                self.emit_status(
                    ThreadCommand('init_lcd',
                                  dict(labels=labels,
                                       Nvals=len(labels),
                                       digits=6,
                                       show_graph=self.settings['lcd', 'lcd_graph'])))
                QtWidgets.QApplication.processEvents()
                self.lcd_init = True

            self.emit_status(ThreadCommand('lcd', dict(values=data_tot,
                                                       show_graph=self.settings['lcd', 'lcd_graph'])))

    def stop(self):
        """
            not implemented.
        """

        return ""


if __name__ == '__main__':
    main(__file__)
