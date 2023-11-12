from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType
from pymodaq_plugins_mock.hardware.wrapper import ActuatorWrapperWithTauMultiAxes
from pymodaq.utils.data import DataActuator
from pymodaq_plugins_mock import config


class DAQ_Move_Mock(DAQ_Move_base):
    """
        Wrapper object to access the Mock fonctionnalities, similar wrapper for all controllers.

        =============== ==============
        **Attributes**    **Type**
        *params*          dictionnary
        =============== ==============
    """
    _controller_units = ActuatorWrapperWithTauMultiAxes.units
    config = config
    is_multiaxes = True  # set to True if this plugin is controlled for a multiaxis controller (with a unique communication link)
    _axis_names = ActuatorWrapperWithTauMultiAxes.axes  # "list of strings of the multiaxes
    _epsilon = 0.01
    data_actuator_type = DataActuatorType['DataActuator']
    params = \
        [
            {'title': 'Tau (ms):', 'name': 'tau', 'type': 'int', 'value': ActuatorWrapperWithTauMultiAxes._tau * 1000,
             'tip': 'Characteristic evolution time'},
             ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.controller: ActuatorWrapperWithTauMultiAxes = None

    def get_actuator_value(self):
        pos = DataActuator(data=self.controller.get_value(self.axis_name))
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
        elif param.name() == 'axis':
            self.settings.child('units').setValue(self.controller.get_units(self.axis_name))
            self.emit_value(self.get_actuator_value())

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
        self.controller: ActuatorWrapperWithTauMultiAxes = self.ini_stage_init(controller,
                                                                               ActuatorWrapperWithTauMultiAxes())
        self.controller.tau = self.settings['tau'] / 1000
        self.settings.child('units').setValue(self.controller.get_units(self.axis_name))
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
        self.target_value = position
        position = self.set_position_with_scaling(position)  # apply scaling if the user specified one

        ## TODO for your custom plugin
        self.controller.move_at(position.value(), self.axis_name)

    def move_rel(self, position):
        """ Move the actuator to the relative target actuator value defined by position

        Parameters
        ----------
        position: (flaot) value of the relative target positioning
        """
        position = self.check_bound(self.current_value+position)-self.current_value
        self.target_value = position + self.current_value
        self.set_position_relative_with_scaling(position)
        self.controller.move_at(self.target_value.value(), self.axis_name)

    def move_home(self):
        """
          Send the update status thread command.
            See Also
            --------
            daq_utils.ThreadCommand
        """

        ## TODO for your custom plugin
        self.controller.move_at(0, self.axis_name)

    def stop_motion(self):
      """
        Call the specific move_done function (depending on the hardware).

        See Also
        --------
        move_done
      """
      self.controller.stop(self.axis_name)
      self.move_done()


if __name__ == '__main__':
    main(__file__)
