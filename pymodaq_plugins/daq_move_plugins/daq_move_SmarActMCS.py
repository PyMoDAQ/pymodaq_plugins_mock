from pymodaq.daq_move.utility_classes import DAQ_Move_base
from pymodaq.daq_move.utility_classes import comon_parameters
from pymodaq.daq_utils.daq_utils import ThreadCommand
from pymodaq.daq_utils.custom_parameter_tree import iter_children
from easydict import EasyDict as edict
from pymodaq_plugins.hardware.smaract.smaract import SmarAct

"""
We suppose to work with Windows OS
We suppose that only one MCS controller is connected to the machine
"""

class DAQ_Move_SmarActMCS(DAQ_Move_base):
    _controller_units = 'nm'

    controller_locator = SmarAct().get_controller_locator()

    is_multiaxes=True
    stage_names=['channel 1','channel 2','channel 3']
    min_bound = -1e6  # nm
    max_bound = +1e6  # nm

    params = [
                 {'title': 'group parameter:', 'name': 'group_parameter', 'type': 'group', 'children': [
                     {'title': 'Controller Name:', 'name': 'SmarAct MCS', 'type': 'str',
                      'value': 'actuator controller', 'readonly': True},
                     {'title': 'Controller locator', 'name': 'controller_locator', 'type': 'list',
                      'value': controller_locator},
                     {'title': 'Controller address:', 'name': 'controller_address', 'type': 'int', 'value': 1,
                      'default': 1, 'min': 1},
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

    def __init__(self,parent=None,params_state=None):
        super(DAQ_Move_SmarActMCS,self).__init__(parent,params_state)

        self.controller=None
        self.settings.child(('epsilon')).setValue(1)

    def ini_stage(self,controller=None):
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
            self.status.update(edict(info="",controller=None,initialized=False))

            #check whether this stage is controlled by a multiaxe controller (to be defined for each plugin)
            # if mutliaxes then init the controller here if Master state otherwise use external controller
            if self.settings.child('multiaxes','ismultiaxes').value() and self.settings.child('multiaxes','multi_status').value()=="Slave":
                if controller is None:
                    raise Exception('no controller has been defined externally while this axe is a slave one')
                else:
                    self.controller=controller
            else: #Master stage
                try:
                    self.close()
                except:
                    pass
                self.controller = SmarAct()
                controller_index = self.controller.init_communication(self.settings.child(('controller_locator')).value())
                self.settings.child(('controller_address')).setValue(controller_index)

            #################################################################
            # we may need to initialize the stages here with SA_SetSensorEnabled
            # or SA_SensorType for example… ???
            ##################################################################
            self.settings.child('bounds', 'is_bounds').setValue(True)
            self.settings.child('bounds', 'min_bound').setValue(self.min_bound)
            self.settings.child('bounds', 'max_bound').setValue(self.max_bound)
            self.settings.child('scaling', 'use_scaling').setValue(False)

            self.status.info = self.settings.child('controller_address').value()
            self.status.controller = self.controller
            self.status.initialized = True
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status',[str(e),'log']))
            self.status.info=str(e)
            self.status.initialized=False
            return self.status

    def close(self):
        """
            close the current instance of Piezo instrument.
        """

        self.controller.close_communication()
        self.controller = None

if __name__ == "__main__":
    test = DAQ_Move_SmarActMCS()