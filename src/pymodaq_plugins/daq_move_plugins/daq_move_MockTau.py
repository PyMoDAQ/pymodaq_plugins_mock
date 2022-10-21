from pymodaq.daq_move.utility_classes import DAQ_Move_base, main, comon_parameters_fun  # base class
from pymodaq.daq_move.utility_classes import comon_parameters  # common set of parameters for all actuators
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo  # object used to send info back to the main thread
from easydict import EasyDict as edict  # type of dict

from pymodaq_plugins.hardware.wrapper import ActuatorWrapper, ActuatorWrapperWithTau

class DAQ_Move_MockTau(DAQ_Move_base):
    """
        Wrapper object to access the Mock fonctionnalities, similar wrapper for all controllers.

        =============== ==============
        **Attributes**    **Type**
        *params*          dictionnary
        =============== ==============
    """
    _controller_units = ActuatorWrapperWithTau.units

    is_multiaxes = False  # set to True if this plugin is controlled for a multiaxis controller (with a unique communication link)
    axes_names = []  # "list of strings of the multiaxes

    params = [
        {'title': 'Tau (ms):', 'name': 'tau', 'type': 'int', 'value': 2000, 'tip': 'Characteristic evolution time'}
        ] + comon_parameters_fun(is_multiaxes, axes_names)

    def get_actuator_value(self):
        # TODO for your custom plugin
        pos = self.controller.get_value()
        pos = self.get_position_with_scaling(pos)
        return pos

    def close(self):
        """
        Terminate the communication protocol
        """
        self.controller.close_communication()

    def commit_settings(self, param):
        if param.name() == 'tau':
            self.controller.tau = param.value() / 1000  # controller need a tau in seconds while the param tau is in ms
        elif param.name() == 'epsilon':
            self.controller.epsilon = param.value()

    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """
        self.controller = self.ini_stage_init(controller, ActuatorWrapperWithTau())
        self.settings.child('tau').setValue(10000)
        info = "Controller initialized"
        initialized = True
        return info, initialized

    def move_abs(self, position):
        """ Move the actuator to the absolute target defined by position

        Parameters
        ----------
        position: (float) value of the absolute target positioning
        """

        position = self.check_bound(position)  #if user checked bounds, the defined bounds are applied here
        position = self.set_position_with_scaling(position)  # apply scaling if the user specified one

        ## TODO for your custom plugin
        self.controller.move_at(position)
        self.target_position = position

    def move_rel(self, position):
        """ Move the actuator to the relative target actuator value defined by position

        Parameters
        ----------
        position: (flaot) value of the relative target positioning
        """
        position = self.check_bound(self.current_position+position)-self.current_position
        self.target_position = position + self.current_position

        ## TODO for your custom plugin
        self.controller.move_at(self.target_position)

    def move_home(self):
        """
          Send the update status thread command.
            See Also
            --------
            daq_utils.ThreadCommand
        """

        ## TODO for your custom plugin
        self.controller.move_at(0)

    def stop_motion(self):
      """
        Call the specific move_done function (depending on the hardware).

        See Also
        --------
        move_done
      """

      ## TODO for your custom plugin
      self.controller.stop()
      #self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))
      self.move_done() #to let the interface know the actuator stopped


if __name__ == '__main__':
    main(__file__)