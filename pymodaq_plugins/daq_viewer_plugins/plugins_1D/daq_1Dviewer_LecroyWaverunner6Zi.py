from PyQt5.QtCore import pyqtSignal
from easydict import EasyDict as edict
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo, DataFromPlugins, Axis
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base
from collections import OrderedDict
import numpy as np
from pymodaq.daq_viewer.utility_classes import comon_parameters

from visa import ResourceManager
# Import the pywin32 library, this library allow the control of other applications.
# Used here for LeCroy.ActiveDSOCtrl.1
# The methods of ActiveDSO are described in the documentation Lecroy ActiveDSO Developers Guide
import win32com.client

# It seems important to initialize active_dso outside the class (???)
# If not pymodaq will not allow the initialization of the detector.
active_dso = win32com.client.Dispatch("LeCroy.ActiveDSOCtrl.1")

"""
Documentation
-------------

The Lecroy documentation can be found at

    pymodaq_plugins/hardware/lecroy_waverunner6Zi

Prerequisite
------------

This plugin has been designed for Lecroy waverunner 6Zi oscilloscopes (tested with waverunner 610Zi).

This plugin necessarily needs a Windows operating system (tested with Windows 7).
You would need to install (at least):

    - Lecroy ActiveDSO : https://teledynelecroy.com/support/softwaredownload/activedso.aspx?capid=106&mid=533&smid=
    - NI-VISA : https://www.ni.com/fr-fr/support/downloads/drivers/download.ni-visa.html#305862
    - pyvisa : https://pyvisa.readthedocs.io/en/latest/index.html

How to use / bugs
-----------------

The user should be aware that the program will probably freeze (and the scope will have to be restarted) in the
following cases :

    - If the user selects in pymodaq a channel that is not activated on the scope
    - If the user change some parameters of the scope (like the horizontal scale) while pymodaq acquisition is running.
        To prevent from this error the user should stop the pymodaq acquisition (STOP button in the GUI interface),
        then change the oscilloscope parameter of his choice, then rerun the acquisition. See also the comments in the
        grab_data function below.

Issues
------

If you see any misbehavior you can raise an issue on the github repository :

    https://github.com/CEMES-CNRS/pymodaq_plugins/issues

"""

class DAQ_1DViewer_LecroyWaverunner6Zi(DAQ_Viewer_base):
    """
        ==================== ========================
        **Attributes**        **Type**
        *data_grabed_signal*  instance of pyqtSignal
        *VISA_rm*             ResourceManager
        *com_ports*
        *params*              dictionnary list
        *keithley*
        *settings*
        ==================== ========================
    """
    data_grabed_signal = pyqtSignal(list)

    ##checking VISA ressources
    VISA_rm = ResourceManager()
    resources = list(VISA_rm.list_resources())

    params = comon_parameters + [
            {'title': 'VISA:',
             'name': 'VISA_ressources',
             'type': 'list',
             'values': resources},
            {'title': 'Channels:',
             'name': 'channels',
             'type': 'itemselect',
             'value': dict(all_items=["C1", "C2", "C3", "C4", "F1", "F2", "F3", "F4"], selected=["C1"])},
        ]

    def __init__(self, parent = None, params_state = None):
        super(DAQ_1DViewer_LecroyWaverunner6Zi, self).__init__(parent, params_state)
        self.controller = None

    def ini_detector(self, controller = None):
        """
            Initialisation procedure of the detector.

            Returns
            -------

                The initialized status.

            See Also
            --------
            daq_utils.ThreadCommand
        """
        self.status.update(edict(initialized = False, info = "", x_axis = None, y_axis = None, controller = None))
        try:
            if self.settings.child(('controller_status')).value() == "Slave":
                if controller is None:
                    raise Exception('no controller has been defined externally while this detector is a slave one')
                else:
                    self.controller = controller
            else:
                self.controller = active_dso
                usb_address = "USBTMC:" + self.settings.child(('VISA_ressources')).value()
                self.controller.MakeConnection(usb_address)
                # set the timeout of the scope to 10 seconds
                # may be not needed
                self.controller.setTimeout(10)

            self.status.initialized = True
            self.status.controller = self.controller
            return self.status
        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))
            self.status.info = getLineInfo() + str(e)
            self.status.initialized = False
            return self.status

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
            pass
        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status',[getLineInfo() + str(e),'log']))

    def grab_data(self, Naverage=1, **kwargs):
        """
            | Start new acquisition.
            | Grab the current values.
            | Send the data_grabed_signal once done.

            =============== ======== ===============================================
            **Parameters**  **Type**  **Description**
            *Naverage*      int       Number of values to average
            =============== ======== ===============================================
        """
        channel = self.settings.child(('channels')).value()['selected']

        # The WaitForOPC method is used to wait for previous commands to be interpreted before continuing
        # It may be not needed here
        if not self.controller.WaitForOPC():
            raise Exception("Wait for OPC error")

        waveform = self.controller.GetScaledWaveformWithTimes(channel[0], 1e8, 0)

        # The ErrorFlag property checks that there is no error concerning ActiveDSO.
        # If the user changes some parameters on the oscilloscope (for example the horizontal scale) while pymodaq
        # acquisition is running, it will raise this error. We do not know how to deal with this problem.
        # If the error is raised you will probably have to restart the oscilloscope to get the communication back.
        # Restarting can be done with a little script using the DeviceClear(True) method of ActiveDSO. It is much
        # faster than doing it manually.
        #
        # To prevent the error, the user should use the STOP button on pymodaq GUI, then change the parameter of his
        # choice on the oscilloscope and then RUN pymodaq acquisition.
        if self.controller.ErrorFlag:
            raise Exception(self.controller.ErrorString)

        x_axis = np.array(waveform[0])
        data = [np.array(waveform[1])]

        self.data_grabed_signal.emit([DataFromPlugins(
            name='Lecroy Waverunner 6Zi',
            data=data,
            dim='Data1D',
            x_axis=Axis(data=x_axis, label='Time', units='s')
        )])

    def stop(self):
        """
            not implemented?
        """
        return ""

    def close(self):
        """
            close the current instance.
        """

        # disconnect the interface with the scope
        self.controller.Disconnect()

