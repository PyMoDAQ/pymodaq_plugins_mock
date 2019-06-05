from pymodaq.daq_move.utility_classes import DAQ_Move_base
from pymodaq.daq_move.utility_classes import comon_parameters
from pymodaq.daq_utils.daq_utils import ThreadCommand
from pymodaq.daq_utils.custom_parameter_tree import iter_children
from easydict import EasyDict as edict
from pymodaq_plugins.hardware.smaract.smaract import SmarAct

"""
We suppose to work with Windows OS (tested with Windows 7)

The support of multiple controllers connected to the machine is not implemented

We suppose that the configuration of the controller (sensor type etc) has been
done via the SmarAct MCS Configuration software

We suppose to have a linear positionner with an enabled sensor attached to it,
connected to the channel 0 of the controller

Tested with SLC-1740-S (closed loop with nanometer precision sensor) connected
to a MCS-3D controller
"""

class DAQ_Move_SmarActMCS(DAQ_Move_base):
    _controller_units = 'nm'

    is_multiaxes = False
    stage_names = ['channel 0']

    params = [
                 {'title': 'group parameter:', 'name': 'group_parameter', 'type': 'group', 'children': [
                     {'title': 'Controller Name:', 'name': 'SmarAct MCS', 'type': 'str',
                      'value': 'actuator controller', 'readonly': True},
                 ]},

                 ##########################################################
                 # the ones below should ALWAYS be present!!!
                 {'title': 'MultiAxes:', 'name': 'multiaxes', 'type': 'group', 'visible': is_multiaxes, 'children': [
                     {'title': 'is Multiaxes:', 'name': 'ismultiaxes', 'type': 'bool', 'value': is_multiaxes,
                      'default': False},
                     {'title': 'Status:', 'name': 'multi_status', 'type': 'list', 'value': 'Master',
                      'values': ['Master', 'Slave']},
                     {'title': 'Axis:', 'name': 'axis', 'type': 'list', 'values': stage_names},

                 ]}] + comon_parameters
                 ##########################################################

    def __init__(self, parent=None, params_state=None):
        super(DAQ_Move_SmarActMCS, self).__init__(parent, params_state)

        self.controller = None
        self.settings.child(('epsilon')).setValue(1)

    def ini_stage(self, controller=None):
        """
            Initialize the controller and stages (axes) with given parameters.

            =============== ================================================ =========================================================================================
            **Parameters**   **Type**                                         **Description**
            *controller*     instance of the specific controller object       If defined this hardware will use it and will not initialize its own controller instance
            =============== ================================================ =========================================================================================

            Returns
            -------
            Easydict
                dictionnary containing keys:
                 * *info* : string displaying various info
                 * *controller*: instance of the controller object in order to control other axes without the need to init the same controller twice
                 * *stage*: instance of the stage (axis or whatever) object
                 * *initialized*: boolean indicating if initialization has been done correctly

            See Also
            --------
            DAQ_utils.ThreadCommand
        """
        try:
            # initialize the stage and its controller status
            # controller is an object that may be passed to other instances of DAQ_Move_Actuator in case
            # of one controller controlling multiaxes
            self.status.update(edict(info="", controller=None, initialized=False))

            #check whether this stage is controlled by a multiaxe controller (to be defined for each plugin)
            # if mutliaxes then init the controller here if Master state otherwise use external controller
            if self.settings.child('multiaxes', 'ismultiaxes').value() and self.settings.child('multiaxes','multi_status').value()=="Slave":
                if controller is None:
                    raise Exception('no controller has been defined externally while this axe is a slave one')
                else:
                    self.controller = controller
            else: #Master stage
                try:
                    self.close()
                except:
                    pass
                self.controller = SmarAct()

            # The min and max bounds will depend on which positionner is plugged. Anyway the bounds are secured
            # by the library functions.
            self.settings.child('bounds', 'is_bounds').setValue(False)
            self.settings.child('scaling', 'use_scaling').setValue(False)

            self.status.controller = self.controller
            self.status.initialized = True

            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [str(e), 'log']))
            self.status.info = str(e)
            self.status.initialized = False

            return self.status

    def close(self):
        """
            Close the communication with the SmarAct controller.
        """

        self.controller.close_communication()
        self.controller = None

    def check_position(self):
        """
            Get the current hardware position with scaling conversion given by get_position_with_scaling.
        """

        position = self.controller.get_position()

        # convert pos if scaling options have been used, mandatory here
        position = self.get_position_with_scaling(position)
        self.current_position = position
        self.emit_status(ThreadCommand('check_position', [position]))

        return position

    def move_Abs(self, position):
        """
            Move to an absolute position
        """
        #limit position if bounds options has been selected and if position is out of them
        position = self.check_bound(position)
        self.target_position = position
        # convert the user set position to the controller position if scaling has been activated by user
        position = self.set_position_with_scaling(position)

        self.controller.absolute_move(position)

        # start polling the position until the actuator reach the target position within epsilon
        # defined as a parameter field (comon_parameters)
        self.poll_moving()

    def move_Rel(self,position):
        """
            Move to a relative position
        """
        # limit position if bounds options has been selected and if position is out of them
        position = self.check_bound(self.current_position + position) - self.current_position
        self.target_position = position + self.current_position
        # convert the user set position to the controller position if scaling has been activated by user
        position = self.set_position_with_scaling(position)

        self.controller.relative_move(position)

        self.poll_moving()

    def move_Home(self):
        """
            Move to home and reset position to zero.
        """

        self.controller.find_reference()

    def stop_motion(self):
        """
            See Also
            --------
            DAQ_Move_base.move_done
        """

        self.controller.stop()

        self.move_done()

if __name__ == "__main__":
    test = DAQ_Move_SmarActMCS()