from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base, comon_parameters
from pymodaq.daq_utils.daq_utils import DataFromPlugins
from easydict import EasyDict as edict
from collections import OrderedDict
from pymodaq_plugins.hardware.keithley2110.keithley2110_VISADriver import Keithley2110VISADriver as Keithley2110

class DAQ_0DViewer_Keithley2110(DAQ_Viewer_base):
    """
        Naive implementation of a DAQ 0D Viewer using the Keithley 2110 as data source
        This DAQ0D Viewer plugin only supports measurement mode selection and a simple data read acquisition mechanism
        with no averaging supported
        =============== =================
        **Attributes**  **Type**
        *params*        dictionnary list
        *x_axis*        1D numpy array
        *ind_data*      int
        =============== =================
    """
    params = comon_parameters+[
        {'title': 'Keithley2210 Parameters',  'name': 'K2110Params', 'type': 'group', 'children': [
            {'title': 'Mode', 'name': 'mode', 'type': 'list', 'values': ['VDC', 'VAC', 'R2W', 'R4W'], 'value': 'VDC'}

        ]}
    ]

    def __init__(self, parent=None, params_state=None): # init_params is a list of tuple where each tuple contains info on a 1D channel (Ntps,amplitude, width, position and noise)
        super(DAQ_0DViewer_Keithley2110, self).__init__(parent, params_state)
        self.x_axis = None
        self.ind_data = 0


    def commit_settings(self, param):
        """
            ============== ========= =================
            **Parameters**  **Type**  **Description**
            *param*        child node  could be the following setting parameter: 'mode'
            ============== ========= =================
        """
        if param.name() == 'mode':
            """Updates the newly selected measurement mode"""
            self.controller.set_mode(param.value())

    def ini_detector(self, controller=None):
        """
            Initialisation procedure of the detector.

            Returns
            -------
                the initialized status.
        """

        self.status.update(edict(initialized=False, info="", x_axis=None, y_axis=None, controller=None))
        if self.settings.child(('controller_status')).value() == "Slave":
            if controller is None: 
                raise Exception('no controller has been defined externally while this detector is a slave one')
            else:
                self.controller = controller
        else:
            try:
                self.controller = Keithley2110('K2110')
            except Exception as e:
                raise Exception('No controller could be defined because an error occurred\
                 while connecting to the instrument. Error: {}'.format(str(e)))

        self.controller.set_mode(self.settings.child('K2110Params', 'mode').value())

        # initialize viewers with the future type of data
        self.data_grabed_signal.emit([DataFromPlugins(name='Keithley2110', data=[0], dim='Data0D', labels=['Meas', 'Time'])])

        self.status.initialized = True
        self.status.controller = self.controller
        return self.status

    def close(self):
        """
            not implemented.
        """
        pass

    def grab_data(self, Naverage=1, **kwargs):
        """
            | Start new acquisition.
            |
            |
            | Send the data_grabed_signal once done.

            =============== ======== ===============================================
            **Parameters**  **Type**  **Description**
            *Naverage*      int       specify the threshold of the mean calculation
            =============== ======== ===============================================

        """
        data = self.controller.read()
        self.data_grabed_signal.emit([utils.DataFromPlugins(name='K2110', data=[[data]], dim='Data0D',)])
        self.ind_data += 1

    def stop(self):
        """
            not implemented.
        """

        return ""
