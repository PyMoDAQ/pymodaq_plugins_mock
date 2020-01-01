from PyQt5.QtCore import QThread
from pymodaq.daq_move.utility_classes import DAQ_Move_base
from pymodaq.daq_move.utility_classes import comon_parameters
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo
from pymodaq_plugins.hardware.Newport.esp100 import ESP100
from easydict import EasyDict as edict
import pyvisa


class DAQ_Move_Newport_ESP100(DAQ_Move_base):
    """

    """

    _controller_units = 'mm'
    _axis = 1

    #find available COM ports
    visa_rm = pyvisa.ResourceManager()
    infos = visa_rm.list_resources_info()
    ports = []
    for k in infos.keys():
        ports.append(infos[k].alias)
    port = 'COM6' if 'COM6' in ports else ports[0] if len(ports) > 0 else ''
    #if ports==[]:
    #    ports.append('')


    is_multiaxes = False
    stage_names = []

    params= [{'title': 'Time interval (ms):', 'name': 'time_interval', 'type': 'int', 'value': 200},
             {'title': 'Controller Info:', 'name': 'controller_id', 'type': 'text', 'value': '', 'readonly': True},
             {'title': 'COM Port:', 'name': 'com_port', 'type': 'list', 'values': ports, 'value': port},
             {'title': 'Velocity:', 'name': 'velocity', 'type': 'float', 'value': 1.0},

            {'title': 'MultiAxes:', 'name': 'multiaxes', 'type': 'group','visible':is_multiaxes, 'children':[
                        {'title': 'is Multiaxes:', 'name': 'ismultiaxes', 'type': 'bool', 'value': is_multiaxes, 'default': False},
                        {'title': 'Status:', 'name': 'multi_status', 'type': 'list', 'value': 'Master', 'values': ['Master', 'Slave']},
                        {'title': 'Axis:', 'name': 'axis', 'type': 'list',  'values': stage_names},
                        
                        ]}]+comon_parameters

    def __init__(self,parent=None,params_state=None):
        super().__init__(parent, params_state)

        self.controller=None
        self.settings.child(('epsilon')).setValue(0.01)

    def ini_stage(self, controller=None):
        """
            Initialize the controller and stages (axes) with given parameters.

            =============== =========================================== ===========================================================================================
            **Parameters**   **Type**                                     **Description**

            *controller*     instance of the specific controller object   If defined this hardware will use it and will not initialize its own controller instance
            =============== =========================================== ===========================================================================================

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

        # initialize the stage and its controller status
        # controller is an object that may be passed to other instances of DAQ_Move_Mock in case
        # of one controller controlling multiaxes
        try:
            self.status.update(edict(info="",controller=None,initialized=False))


            #check whether this stage is controlled by a multiaxe controller (to be defined for each plugin)

            # if mutliaxes then init the controller here if Master state otherwise use external controller
            if self.settings.child('multiaxes', 'ismultiaxes').value() and self.settings.child('multiaxes','multi_status').value()=="Slave":
                if controller is None: 
                    raise Exception('no controller has been defined externally while this stage is a slave one')
                else:
                    self.controller = controller
            else: #Master stage
                try:
                    self.close()
                except:
                    pass
                self.controller = ESP100()
                self.controller.init_communication(self.settings.child(('com_port')).value(), self._axis)

            controller_id = self.controller.get_controller_infos()
            self.settings.child(('controller_id')).setValue(controller_id)
            self.settings.child(('velocity')).setValue(self.controller.get_velocity(self._axis))
            self.settings.child(('velocity')).setOpts(max=self.controller.get_velocity_max(self._axis))
            self.settings.child(('epsilon')).setValue(0.1)
            self.status.info = controller_id
            self.status.controller = self.controller
            self.status.initialized = True
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo()+ str(e), 'log']))
            self.status.info = getLineInfo()+ str(e)
            self.status.initialized = False
            return self.status

    def commit_settings(self,param):
        """
        to subclass to transfer parameters to hardware
        """
        if param.name() == 'velocity':
            self.controller.set_velocity(param.value(), self._axis)

    def close(self):
        """
            close the current instance of Piezo instrument.
        """
        self.controller.close_communication(self._axis)
        self.controller = None


    def check_position(self):
        """
            Check the current position from the hardware.

            Returns
            -------
            float
                The position of the hardware.

            See Also
            --------
            DAQ_Move_base.get_position_with_scaling, daq_utils.ThreadCommand
        """
        position = self.controller.get_position(self._axis)
        pos = self.get_position_with_scaling(position)
        self.current_position = pos
        self.emit_status(ThreadCommand('check_position', [pos]))
        return self.target_position



    def move_Abs(self,position):
        """

        Parameters
        ----------
        position: (float) target position of the given axis in um (or scaled units)

        Returns
        -------

        """
        position = self.check_bound(position)  #limits the position within the specified bounds (-100,100)
        self.target_position = position

        #get positions in controller units
        position = self.set_position_with_scaling(position)
        out = self.controller.move_axis('ABS', self._axis, position)

        self.poll_moving()


    def move_Rel(self,position):
        """
            Make the hardware relative move of the Piezo instrument from the given position after thread command signal was received in DAQ_Move_main.

            =============== ========= =======================
            **Parameters**  **Type**   **Description**

            *position*       float     The absolute position
            =============== ========= =======================

            See Also
            --------
            DAQ_Move_base.set_position_with_scaling, DAQ_Move_base.poll_moving

        """
        position = self.check_bound(self.current_position+position)-self.current_position
        self.target_position = position+self.current_position
        position = self.set_position_relative_with_scaling(position)

        out = self.controller.move_axis('REL', self._axis, pos)
        QThread.msleep(50)  # to make sure the closed loop converged
        self.poll_moving()

    def move_Home(self):
        """
            Move to the absolute vlue 100 corresponding the default point of the Piezo instrument.

            See Also
            --------
            DAQ_Move_base.move_Abs
        """
        self.controller.move_home()

    def stop_motion(self):
      """
        Call the specific move_done function (depending on the hardware).

        See Also
        --------
        move_done
      """
      self.controller.stop_motion()
