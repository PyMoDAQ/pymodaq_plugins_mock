from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, main  # base class
from pymodaq.control_modules.move_utility_classes import comon_parameters_fun  # common set of parameters for all actuators
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo  # object used to send info back to the main thread
from easydict import EasyDict as edict  # type of dict

from pymodaq_plugins_mock.hardware.camera_wrapper import Camera

class DAQ_Move_MockCamera(DAQ_Move_base):
    """
        Wrapper object to access the Mock fonctionnalities, similar wrapper for all controllers.

        =============== ==============
        **Attributes**    **Type**
        *params*          dictionnary
        =============== ==============
    """
    _controller_units = 'whatever'
    is_multiaxes = True
    stage_names = Camera.axes
    _epsilon = 0.01

    params = comon_parameters_fun(is_multiaxes, stage_names)

    def ini_attributes(self):
        self.controller: Camera = None

    def get_actuator_value(self):
        axis = self.settings['multiaxes', 'axis']
        pos = self.controller.get_value(axis)
        pos = self.get_position_with_scaling(pos)
        return pos

    def close(self):
        pass

    def commit_settings(self, param):
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
        self.ini_stage_init(controller, Camera())
        info = "Mock Camera"
        initialized = True
        return info, initialized

    def move_abs(self, position):
        position = self.check_bound(position)  #if user checked bounds, the defined bounds are applied here
        self.target_value = position
        position = self.set_position_with_scaling(position)
        axis = self.settings['multiaxes', 'axis']
        pos = self.controller.set_value(axis, position)

    def move_rel(self, position):
        position = self.check_bound(self.current_position + position) - self.current_position
        self.target_value = position + self.current_position
        position = self.set_position_with_scaling(self.target_value)

        axis = self.settings['multiaxes', 'axis']
        pos = self.controller.set_value(axis, position)

    def move_home(self):
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