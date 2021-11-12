from pymodaq.daq_move.utility_classes import DAQ_Move_base  # base class
from pymodaq.daq_move.utility_classes import comon_parameters  # common set of parameters for all actuators
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo  # object used to send info back to the main thread
from easydict import EasyDict as edict  # type of dict

from ..hardware.wrapper import ActuatorWrapper, ActuatorWrapperWithTau

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
    stage_names = []  # "list of strings of the multiaxes

    params = [
        {'title': 'Com port:', 'name': 'comport', 'type': 'str', 'value': 'COM28', 'tip': 'The serial COM port'},
        {'title': 'Tau (ms):', 'name': 'tau', 'type': 'int', 'value': 2000, 'tip': 'Characteristic evolution time'}
        ] + [   ## TODO for your custom plugin
                 # elements to be added here as dicts in order to control your custom stage
                 ############
                 {'title': 'MultiAxes:', 'name': 'multiaxes', 'type': 'group', 'visible': is_multiaxes, 'children': [
                     {'title': 'is Multiaxes:', 'name': 'ismultiaxes', 'type': 'bool', 'value': is_multiaxes,
                      'default': False},
                     {'title': 'Status:', 'name': 'multi_status', 'type': 'list', 'value': 'Master',
                      'limits': ['Master', 'Slave']},
                     {'title': 'Axis:', 'name': 'axis', 'type': 'list', 'limits': stage_names},

                 ]}] + comon_parameters

    def __init__(self, parent=None, params_state=None):
        """
            Initialize the the class

            ============== ================================================ ==========================================================================================
            **Parameters**  **Type**                                         **Description**

            *parent*        Caller object of this plugin                    see DAQ_Move_main.DAQ_Move_stage
            *params_state*  list of dicts                                   saved state of the plugins parameters list
            ============== ================================================ ==========================================================================================

        """

        super().__init__(parent, params_state)


    def check_position(self):
        """Get the current position from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        # TODO for your custom plugin
        pos = self.controller.get_value()
        ##

        pos = self.get_position_with_scaling(pos)
        self.emit_status(ThreadCommand('check_position',[pos]))
        return pos


    def close(self):
        """
        Terminate the communication protocol
        """
        # TODO for your custom plugin
        self.controller.close_communication()
        ##

    def commit_settings(self, param):
        if param.name() == 'tau':
            self.controller.tau = param.value() / 1000  # controller need a tau in seconds while the param tau is in ms
        elif param.name() == 'epsilon':
            self.controller.epsilon = param.value()

    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object) custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

        Returns
        -------
        self.status (edict): with initialization status: three fields:
            * info (str)
            * controller (object) initialized controller
            *initialized: (bool): False if initialization failed otherwise True
        """


        try:
            # initialize the stage and its controller status
            # controller is an object that may be passed to other instances of DAQ_Move_Mock in case
            # of one controller controlling multiactuators (or detector)

            self.status.update(edict(info="", controller=None, initialized=False))

            # check whether this stage is controlled by a multiaxe controller (to be defined for each plugin)
            # if multiaxes then init the controller here if Master state otherwise use external controller
            if self.settings.child('multiaxes', 'ismultiaxes').value() and self.settings.child('multiaxes',
                                   'multi_status').value() == "Slave":
                if controller is None:
                    raise Exception('no controller has been defined externally while this axe is a slave one')
                else:
                    self.controller = controller
            else:  # Master stage
                self.controller = ActuatorWrapperWithTau()
                ## TODO for your custom plugin

                comport = self.settings.child('comport').value()

                self.controller.open_communication(comport)  # any object that will control the stages
                #####################################

            self.status.info = "Controller initialized"
            self.status.controller = self.controller
            self.status.initialized = True
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))
            self.status.info = getLineInfo() + str(e)
            self.status.initialized = False
            return self.status

    def move_Abs(self, position):
        """ Move the actuator to the absolute target defined by position

        Parameters
        ----------
        position: (flaot) value of the absolute target positioning
        """

        position = self.check_bound(position)  #if user checked bounds, the defined bounds are applied here
        position = self.set_position_with_scaling(position)  # apply scaling if the user specified one

        ## TODO for your custom plugin
        self.controller.move_at(position)
        #self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))
        ##############################



        self.target_position = position
        self.poll_moving()  #start a loop to poll the current actuator value and compare it with target position

    def move_Rel(self, position):
        """ Move the actuator to the relative target actuator value defined by position

        Parameters
        ----------
        position: (flaot) value of the relative target positioning
        """
        position = self.check_bound(self.current_position+position)-self.current_position
        self.target_position = position + self.current_position

        ## TODO for your custom plugin
        self.controller.move_at(self.target_position)
        #self.emit_status(ThreadCommand('Update_Status',['Some info you want to log']))
        ##############################

        self.poll_moving()

    def move_Home(self):
        """
          Send the update status thread command.
            See Also
            --------
            daq_utils.ThreadCommand
        """

        ## TODO for your custom plugin
        self.controller.move_at(0)
        #self.emit_status(ThreadCommand('Update_Status',['Some info you want to log']))
        ##############################


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
      ##############################


