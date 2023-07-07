from qtpy.QtCore import QThread
from qtpy import QtWidgets
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, main
import numpy as np
from easydict import EasyDict as edict
from pymodaq.utils.daq_utils import ThreadCommand, getLineInfo
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq.utils.math_utils import gauss1D, linspace_step
from pymodaq.control_modules.viewer_utility_classes import comon_parameters
from pymodaq.utils.parameter.utils import iter_children


class DAQ_1DViewer_Mock_spectro(DAQ_Viewer_base):
    """
    1D viewer plugin simulating a photon spectrometer controlling the laser source, the exposure and the calibration axis
    Produces one data signal with two hypergaussians whose parameters are fully controllable or
    produces 2 data signals, each beeing a fully controllable hypergaussian
    Features specific methods that should be present for spectrometer features using Pymodaq_spectrometer package:

    get_laser_wl: emit the value of the currently selected laser (if available)
    set_laser_wl: try to set the selected laser wavelength (if applicable), emit the value of the new one

    get_spectro_wl: emit the value of the central frequency
    set_spectro_wl: set the newly central frequency

    get_exposure_ms: emit the value of the exposure time in ms
    set_exposure_ms: set the new exposure time in ms


    """
    params = comon_parameters + [
        {'title': 'Rolling?:', 'name': 'rolling', 'type': 'int', 'value': 0, 'min': 0},
        {'title': 'Multi Channels?:', 'name': 'multi', 'type': 'bool', 'value': False,
         'tip': 'if true, plugin produces multiple curves (2) otherwise produces one curve with 2 peaks'},
        {'title': 'Mock1:', 'name': 'Mock1', 'type': 'group', 'children': [
            {'title': 'Amp:', 'name': 'Amp', 'type': 'int', 'value': 20, 'default': 20},
            {'title': 'x0:', 'name': 'x0', 'type': 'float', 'value': 500, 'default': 500},
            {'title': 'dx:', 'name': 'dx', 'type': 'float', 'value': 0.3, 'default': 20},
            {'title': 'n:', 'name': 'n', 'type': 'int', 'value': 1, 'default': 1, 'min': 1},
            {'title': 'noise:', 'name': 'amp_noise', 'type': 'float', 'value': 0.1, 'default': 0.1, 'min': 0}
        ]},
        {'title': 'Mock2:', 'name': 'Mock2', 'type': 'group', 'children': [
            {'title': 'Amp?:', 'name': 'Amp', 'type': 'int', 'value': 10},
            {'title': 'x0:', 'name': 'x0', 'type': 'float', 'value': 520},
            {'title': 'dx:', 'name': 'dx', 'type': 'float', 'value': 0.7},
            {'title': 'n:', 'name': 'n', 'type': 'int', 'value': 2, 'default': 2, 'min': 1},
            {'title': 'noise:', 'name': 'amp_noise', 'type': 'float', 'value': 0.1, 'default': 0.1, 'min': 0}, ]},

        {'title': 'xaxis:', 'name': 'x_axis', 'type': 'group', 'children': [
            {'title': 'Npts:', 'name': 'Npts', 'type': 'int', 'value': 513, },
            {'title': 'x0:', 'name': 'x0', 'type': 'float', 'value': 515, },
            {'title': 'dx:', 'name': 'dx', 'type': 'float', 'value': 0.1, },
        ]},
        {'title': 'Laser Wavelength', 'name': 'laser_wl', 'type': 'list', 'value': 515, 'limits': [405, 515, 632.8]},
        {'title': 'Exposure (ms)', 'name': 'exposure_ms', 'type': 'int', 'value': 100, 'default': 100}
    ]
    hardware_averaging = False

    def __init__(self, parent=None,
                 params_state=None):  # init_params is a list of tuple where each tuple contains info on a 1D channel (Ntps,amplitude, width, position and noise)
        super().__init__(parent, params_state)

        self.x_axis: Axis = None
        self.ind_data = 0
        self._update_x_axis = True

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
        if param.name() in iter_children(self.settings.child('x_axis'), []):
            if param.name() == 'x0':
                self.get_spectro_wl()
            self.set_x_axis()
        else:
            self.set_Mock_data()

    def set_Mock_data(self):
        """
            For each parameter of the settings tree :
                * compute linspace numpy distribution with local parameters values
                * shift right the current data of ind_data position
                * add computed results to the data_mock list

            Returns
            -------
            list
                The computed data_mock list.
        """
        ind = -1
        self.data_mock = []
        data = np.zeros((self.x_axis.size, ))
        exposure_factor = self.settings['exposure_ms'] / \
            self.settings.child('exposure_ms').opts['default']

        for param in self.settings.children():  #
            if 'Mock' in param.name():
                ind += 1

                data_tmp = exposure_factor * \
                    param['Amp'] * gauss1D(self.x_axis.get_data(), param.child('x0').value(),
                                           param.child('dx').value(),
                                           param.child('n').value())
                if ind == 0:
                    data_tmp = data_tmp * np.sin(self.x_axis.get_data() / 4) ** 2
                data_tmp += param['amp_noise'] * np.random.rand((self.x_axis.size))
                data_tmp = self.settings['exposure_ms'] /\
                    1000 * np.roll(data_tmp, self.ind_data * self.settings['rolling'])
                if self.settings['multi']:
                    self.data_mock.append(data_tmp)
                else:
                    data += data_tmp
        if not self.settings['multi']:
            self.data_mock.append(data)
        self.ind_data += 1
        return self.data_mock

    def set_x_axis(self):
        Npts = self.settings['x_axis', 'Npts']
        x0 = self.settings['x_axis', 'x0']
        dx = self.settings['x_axis', 'dx']
        self.x_axis = Axis(label='photon wavelength', units='nm',
                           data=linspace_step(x0 - (Npts - 1) * dx / 2, x0 + (Npts - 1) * dx / 2, dx),
                           index=0)
        self._update_x_axis = True

    def set_spectro_wl(self, spectro_wl):
        """
        Method related to spectrometer module, mandatory
        Parameters
        ----------
        spectro_wl: set the "grating" position

        """
        self.settings.child('x_axis', 'x0').setValue(spectro_wl)
        QtWidgets.QApplication.processEvents()
        self.emit_status(ThreadCommand('spectro_wl', [self.settings['x_axis', 'x0']]))
        self.set_x_axis()

    def get_spectro_wl(self):
        """
        Method related to spectrometer module, mandatory
        Get the "grating" position
        """
        self.emit_status(ThreadCommand('spectro_wl', [self.settings['x_axis', 'x0']]))

    def get_laser_wl(self):
        """
        Method related to spectrometer module, mandatory if laser can be set
        Get the "laser" position
        """
        self.emit_status(ThreadCommand('laser_wl', [self.settings["laser_wl"]]))

    def set_laser_wl(self, laser_wl):
        """
        Method related to spectrometer module, mandatory if laser can be set
        Set the "laser" position
        """
        self.settings.child("laser_wl").setValue(laser_wl)
        QtWidgets.QApplication.processEvents()
        self.emit_status(ThreadCommand('laser_wl', [self.settings['laser_wl']]))

    def get_exposure_ms(self):
        self.emit_status(ThreadCommand('exposure_ms', [self.settings['exposure_ms']]))

    def set_exposure_ms(self, exposure):
        self.settings.child("exposure_ms").setValue(exposure)
        QtWidgets.QApplication.processEvents()
        self.emit_status(ThreadCommand('exposure_ms', [self.settings['exposure_ms']]))

    def ini_detector(self, controller=None):
        """
            Initialisation procedure of the detector updating the status dictionnary.

            See Also
            --------
            set_Mock_data, daq_utils.ThreadCommand
        """
        self.status.update(edict(initialized=False, info="", x_axis=None, y_axis=None, controller=None))
        try:

            if self.settings['controller_status'] == "Slave":
                if controller is None:
                    raise Exception('no controller has been defined externally while this detector is a slave one')
                else:
                    self.controller = controller
            else:
                self.controller = "Mock controller"
            self.set_x_axis()
            self.set_Mock_data()

            # initialize viewers with the future type of data
            self.dte_signal_temp.emit(DataToExport('Mock1D',
                                                   data=[DataFromPlugins(name='Mock1', data=self.data_mock,
                                                                         dim='Data1D',
                                                                         axes=[self.x_axis],
                                                                         labels=['Mock1', 'label2']),]))

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
        pass

    def grab_data(self, Naverage=1, **kwargs):
        """
            | Start new acquisition

            For each integer step of naverage range:
                * set mock data
                * wait 100 ms
                * update the data_tot array

            | Send the data_grabed_signal once done.

            =============== ======== ===============================================
            **Parameters**  **Type**  **Description**
            *Naverage*      int       Number of spectrum to average.
                                      Specify the threshold of the mean calculation
            =============== ======== ===============================================

            See Also
            --------
            set_Mock_data
        """
        Naverage = 1
        data_tot = self.set_Mock_data()
        for ind in range(Naverage - 1):
            data_tmp = self.set_Mock_data()
            QThread.msleep(self.settings.child('exposure_ms').value())

            for ind, data in enumerate(data_tmp):
                data_tot[ind] += data

        data_tot = [data / Naverage for data in data_tot]
        QThread.msleep(self.settings.child('exposure_ms').value())
        if not self._update_x_axis:
            self.dte_signal.emit(DataToExport('Mock1D',
                                              data=[DataFromPlugins(name='Mock1D', data=data_tot, dim='Data1D',)]))
        else:
            self.dte_signal.emit(DataToExport('Mock1D',
                                              data=[DataFromPlugins(name='Mock1D', data=data_tot, dim='Data1D',
                                                                    axes=[self.x_axis])]))
            self._update_x_axis = False

    def stop(self):
        """
            not implemented.
        """

        return ""

if __name__ == '__main__':
    main(__file__)
