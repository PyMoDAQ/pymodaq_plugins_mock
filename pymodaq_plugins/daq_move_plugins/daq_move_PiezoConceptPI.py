from PyQt5.QtCore import QThread
from pymodaq.daq_move.utility_classes import DAQ_Move_base
from pymodaq.daq_move.utility_classes import comon_parameters
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo
from easydict import EasyDict as edict
from pymodaq_plugins.hardware.piezoconcept.piezoconcept import PiezoConceptPI, Position, Time

class DAQ_Move_PiezoConceptPI(DAQ_Move_base):
    """
    Plugin to drive piezoconcpet XY (Z) stages. There is a string nonlinear offset between the set position and the read
    position. It seems to bnot be problem in the sens where a given displacement is maintained. But because the read
    position is not "accurate", I've decided to ignore it and just trust the set position. So the return will be always
    strictly equal to the set position. However, if there is more that 10% difference raise a warning
    """

    _controller_units = 'µm'

    #find available COM ports
    import serial.tools.list_ports
    ports = [str(port)[0:4] for port in list(serial.tools.list_ports.comports())]
    port = 'COM6' if 'COM6' in ports else ports[0] if len(ports) > 0 else ''
    #if ports==[]:
    #    ports.append('')


    is_multiaxes = True
    stage_names = ['X', 'Y', 'Z']
    min_bound = -95  #*µm
    max_bound = 95  #µm
    offset = 100  #µm

    params= [{'title': 'Time interval (ms):', 'name': 'time_interval', 'type': 'int', 'value': 200},
             {'title': 'Controller Info:', 'name': 'controller_id', 'type': 'text', 'value': '', 'readonly': True},
             {'title': 'COM Port:', 'name': 'com_port', 'type': 'list', 'values': ports, 'value': port},
              {'title': 'MultiAxes:', 'name': 'multiaxes', 'type': 'group','visible':is_multiaxes, 'children':[
                        {'title': 'is Multiaxes:', 'name': 'ismultiaxes', 'type': 'bool', 'value': is_multiaxes, 'default': False},
                        {'title': 'Status:', 'name': 'multi_status', 'type': 'list', 'value': 'Master', 'values': ['Master', 'Slave']},
                        {'title': 'Axis:', 'name': 'axis', 'type': 'list',  'values':stage_names},
                        
                        ]}]+comon_parameters

    def __init__(self,parent=None,params_state=None):
        super().__init__(parent, params_state)

        self.controller=None
        self.settings.child(('epsilon')).setValue(3)

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
                self.controller = PiezoConceptPI()
                self.controller.init_communication(self.settings.child(('com_port')).value())

            controller_id = self.controller.get_controller_infos()
            self.settings.child(('controller_id')).setValue(controller_id)

            self.settings.child('bounds', 'is_bounds').setValue(True)
            self.settings.child('bounds', 'min_bound').setValue(self.min_bound)
            self.settings.child('bounds', 'max_bound').setValue(self.max_bound)
            self.settings.child('scaling', 'use_scaling').setValue(True)
            self.settings.child('scaling', 'offset').setValue(self.offset)

            self.move_Abs(0)


            self.settings.child(('epsilon')).setValue(2)
            self.status.info = controller_id
            self.status.controller = self.controller
            self.status.initialized = True
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo()+ str(e), 'log']))
            self.status.info = getLineInfo()+ str(e)
            self.status.initialized = False
            return self.status

    def close(self):
        """
            close the current instance of Piezo instrument.
        """
        try:
            self.move_Abs(0)
            QThread.msleep(1000)
        except:
            pass


        self.controller.close_communication()
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
        position = self.controller.get_position(self.settings.child('multiaxes', 'axis').value())  #in
        if position.unit == 'n':
            pos = position.pos/1000  # in um
        else:
            pos = position.pos
        pos = self.get_position_with_scaling(pos)
        self.current_position = pos  #should be pos but not precise enough conpared to set position
        self.emit_status(ThreadCommand('check_position', [pos]))
        #print(pos)
        return pos



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
        pos = Position(self.settings.child('multiaxes', 'axis').value(), int(position*1000), unit='n')
        out = self.controller.move_axis('ABS', pos)
        #self.move_is_done = True
        QThread.msleep(50) #to make sure the closed loop converged
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

        pos = Position(self.settings.child('multiaxes', 'axis').value(), position*1000, unit='n')  # always use microns for simplicity
        out = self.controller.move_axis('REL', pos)
        QThread.msleep(50)  # to make sure the closed loop converged
        self.poll_moving()

    def move_Home(self):
        """
            Move to the absolute vlue 100 corresponding the default point of the Piezo instrument.

            See Also
            --------
            DAQ_Move_base.move_Abs
        """
        self.move_Abs(100) #put the axis on the middle position so 100µm

    def stop_motion(self):
      """
        Call the specific move_done function (depending on the hardware).

        See Also
        --------
        move_done
      """
      self.move_done()
