import sys
from PyQt5.QtCore import QThread
from easydict import EasyDict as edict
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base
from collections import OrderedDict
import numpy as np
import clr
from pymodaq.daq_viewer.utility_classes import comon_parameters



class DAQ_0DViewer_Kinesis_KPA101(DAQ_Viewer_base):
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
    ##checking VISA ressources

    _controller_units = 'V'
    kinesis_path = 'C:\\Program Files\\Thorlabs\\Kinesis'

    try:
        sys.path.append(kinesis_path)
        clr.AddReference("Thorlabs.MotionControl.DeviceManagerCLI")
        clr.AddReference("Thorlabs.MotionControl.KCube.PositionAlignerCLI")
        import Thorlabs.MotionControl.DeviceManagerCLI as Device
        import Thorlabs.MotionControl.KCube.PositionAlignerCLI as PosAligner
        Device.DeviceManagerCLI.BuildDeviceList()
        # %%
        serialnumbers = [str(ser) for ser in
                         Device.DeviceManagerCLI.GetDeviceList(PosAligner.KCubePositionAligner.DevicePrefix)]
        # %%

    except:
        serialnumbers=[]

    params = comon_parameters+[
            {'title': 'Kinesis library:', 'name': 'kinesis_lib', 'type': 'browsepath', 'value': kinesis_path},
            {'title': 'Serial number:', 'name': 'serial_number', 'type': 'list', 'values': serialnumbers},
            {'title': 'Device:', 'name': 'device_name', 'type': 'str', 'value': ''},
            {'title': 'Polling time (ms):', 'name': 'polling_time', 'type': 'int', 'value': 250},
            ]

    def __init__(self, parent=None, params_state=None):
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
                self.Device.DeviceManagerCLI.BuildDeviceList()
                serialnumbers = self.Device.DeviceManagerCLI.GetDeviceList(self.PosAligner.KCubePositionAligner.DevicePrefix)
                ser_bool = self.settings.child(('serial_number')).value() in serialnumbers
                if ser_bool:
                    self.controller = self.PosAligner.KCubePositionAligner.CreateKCubePositionAligner(
                        self.settings.child(('serial_number')).value())
                    self.controller.Connect(self.settings.child(('serial_number')).value())
                    if not self.controller.IsSettingsInitialized():
                        self.controller.WaitForSettingsInitialized(5000)
                    self.controller.StartPolling(self.settings.child(('polling_time')).value())
                    self.emit_status(ThreadCommand('update_main_settings', [['wait_time'],
                                                            self.settings.child(('polling_time')).value(), 'value']))
                    QThread.msleep(500)
                    self.controller.EnableDevice()
                    QThread.msleep(500)
                    deviceInfo = self.controller.GetDeviceInfo()
                    self.settings.child(('device_name')).setValue(deviceInfo.Name)

                else:
                    raise Exception("Not valid serial number")

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
            if param.name() == 'kinesis_lib':
                try:
                    sys.path.append(param.value())
                    clr.AddReference("Thorlabs.MotionControl.DeviceManagerCLI")
                    clr.AddReference("Thorlabs.MotionControl.IntegratedStepperMotorsCLI")
                    clr.AddReference("Thorlabs.MotionControl.GenericMotorCLI")
                    import Thorlabs.MotionControl.IntegratedStepperMotorsCLI as Integrated
                    import Thorlabs.MotionControl.DeviceManagerCLI as Device
                    import Thorlabs.MotionControl.GenericMotorCLI as Generic
                    Device.DeviceManagerCLI.BuildDeviceList()
                    serialnumbers = [str(ser) for ser in
                                     Device.DeviceManagerCLI.GetDeviceList(Integrated.CageRotator.DevicePrefix)]

                except:
                    serialnumbers = []
                self.settings.child(('serial_number')).setOpts(limits=serialnumbers)

            elif param.name() == 'polling_time':
                self.controller.StopPolling()
                QThread.msleep(500)
                self.controller.StartPolling(self.settings.child(('polling_time')).value())
                QThread.msleep(500)
                self.emit_status(ThreadCommand('update_main_settings', [['wait_time'], param.value(), 'value']))


        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))

    def close(self):
        """
            close the current instance of Keithley viewer.
        """
        self.controller.DisableDevice()
        self.controller.StopPolling()
        self.controller.Disconnect(False)

    def grab_data(self, Naverage=1, **kwargs):
        """
            | Start new acquisition.
            | grab the current values with keithley profile procedure.
            | Send the data_grabed_signal once done.

            =============== ======== ===============================================
            **Parameters**  **Type**  **Description**
            *Naverage*      int       Number of values to average
            =============== ======== ===============================================
        """
        status = self.controller.Status
        data = [np.array([status.PositionDifference.X]), np.array([status.PositionDifference.Y])]
        data_intens = [np.array([status.Sum])]
        self.data_grabed_signal.emit([OrderedDict(name='KPA101 Positions', data=data, type='Data0D', labels=['X (V)', 'Y (V)'],),
                                      OrderedDict(name='KPA101 Intensity', data=data_intens, type='Data0D', labels=['Intensity'],)])


    def stop(self):
        """
            not implemented?
        """
        return ""
