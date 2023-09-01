from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, main  # base class
from pymodaq.control_modules.move_utility_classes import comon_parameters_fun, DataActuatorType  # common set of parameters for all actuators
from pymodaq.utils.daq_utils import ThreadCommand, getLineInfo  # object used to send info back to the main thread
from easydict import EasyDict as edict  # type of dict

from pymodaq_plugins_mock import config

if 'Mock' not in config('displayed', 'actuators'):
    raise ValueError('Plugin configured to be not displayed')


class DAQ_Move_Mock(DAQ_Move_base):
    """
        Wrapper object to access the Mock fonctionnalities, similar wrapper for all controllers.

        =============== ==============
        **Attributes**    **Type**
        *params*          dictionnary
        =============== ==============
    """
    _controller_units = 'whatever'
    is_multiaxes = False
    stage_names = []
    data_actuator_type = DataActuatorType['DataActuator']

    params = comon_parameters_fun(is_multiaxes, stage_names)

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
        """
            Get the current position from the hardware with scaling conversion.

            Returns
            -------
            float
                The position obtained after scaling conversion.

            See Also
            --------
            DAQ_Move_base.get_position_with_scaling, daq_utils.ThreadCommand
        """
        pos = self.current_position
        # print('Pos from controller is {}'.format(pos))
        # pos=self.get_position_with_scaling(pos)
        # self.current_position=pos
        self.emit_value(pos)
        return pos

    def close(self):
        """
          not implemented.
        """
        pass

    def commit_settings(self, param):
        """
            | Activate any parameter changes on the PI_GCS2 hardware.
            |
            | Called after a param_tree_changed signal from DAQ_Move_main.

        """

        pass

    def ini_stage(self, controller=None):
        """
            Initialize the controller and stages (axes) with given parameters.

            ============== ================================================ ==========================================================================================
            **Parameters**  **Type**                                         **Description**

            *controller*    instance of the specific controller object       If defined this hardware will use it and will not initialize its own controller instance
            ============== ================================================ ==========================================================================================

            Returns
            -------
            Easydict
                dictionnary containing keys:
                 * *info* : string displaying various info
                 * *controller*: instance of the controller object in order to control other axes without the need to init the same controller twice
                 * *stage*: instance of the stage (axis or whatever) object
                 * *initialized*: boolean indicating if initialization has been done corretly

            See Also
            --------
             daq_utils.ThreadCommand
        """
        try:
            # initialize the stage and its controller status
            # controller is an object that may be passed to other instances of DAQ_Move_Mock in case
            # of one controller controlling multiaxes

            self.status.update(edict(info="", controller=None, initialized=False))

            # check whether this stage is controlled by a multiaxe controller (to be defined for each plugin)

            # if mutliaxes then init the controller here if Master state otherwise use external controller
            if self.settings.child('multiaxes', 'ismultiaxes').value() and self.settings.child('multiaxes',
                                                                                               'multi_status').value() == "Slave":
                if controller is None:
                    raise Exception('no controller has been defined externally while this axe is a slave one')
                else:
                    self.controller = controller
            else:  # Master stage
                self.controller = "master_controller"  # any object that will control the stages

            info = "Mock stage"
            self.status.info = info
            self.status.controller = self.controller
            self.status.initialized = True
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))
            self.status.info = getLineInfo() + str(e)
            self.status.initialized = False
            return self.status

    def move_abs(self, position):
        """
        """
        position = self.check_bound(position)
        self.target_position = position

        self.current_position = position  # +np.random.rand()-0.5

    def move_rel(self, position):
        """

        """
        position = self.check_bound(self.current_position + position) - self.current_position
        self.target_position = position + self.current_position

        self.current_position = self.target_position  # +np.random.rand()-0.5

    def move_Home(self):
        """
          Send the update status thread command.
            See Also
            --------
            daq_utils.ThreadCommand
        """
        self.emit_status(ThreadCommand('Update_Status', ['Move Home not implemented']))

    def stop_motion(self):
        """
          Call the specific move_done function (depending on the hardware).

          See Also
          --------
          move_done
        """
        self.move_done()


if __name__ == '__main__':
    main(__file__)
