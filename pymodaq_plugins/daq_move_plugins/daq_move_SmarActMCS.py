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

    params = [
                 {'title': 'group parameter:', 'name': 'group_parameter', 'type': 'group', 'children': [
                     {'title': 'Controller Name:', 'name': 'SmarAct MCS', 'type': 'str',
                      'value': 'actuator controller', 'readonly': True},
                     {'title': 'Controller locator', 'name': 'controller_locator', 'type': 'str',
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

        #wahtever has to be initialized here (not yet the controller but it could be the loaing of the dll, wrapper...
        try:
            #for instance from the conex plugin
            sys.path.append(self.settings.child(('conex_lib')).value())
            clr.AddReference("ConexAGAPCmdLib")
            import Newport.ConexAGAPCmdLib as Conexcmd
            self.controller=Conexcmd.ConexAGAPCmds()


            #set the bound options to True (present in comon_parameters)
            self.settings.child('bounds','is_bounds').setValue(True)
            self.settings.child('bounds','min_bound').setValue(-0.02)
            self.settings.child('bounds','max_bound').setValue(0.02)

        except Exception as e:
            self.emit_status(ThreadCommand("Update_Status",[str(e)]))
            raise Exception(str(e))

if __name__ == "__main__":
    test = DAQ_Move_SmarActMCS()