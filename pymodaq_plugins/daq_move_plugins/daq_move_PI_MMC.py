"""
this plugin use an old dll from PI MMC-DLL not compatible with their new GCS-command stuff
The dll is 32 bits only so should be used with a 32bits python distribution
C-862 Mercury™-DC Motor Controller
C-863 Mercury™-DC Motor Controller
C-663 Mercury™-Step Motor Controller
C-170 Redstone PILine® Controller

"""

import sys, os
from PyQt5.QtCore import QThread
from pymodaq.daq_move.utility_classes import DAQ_Move_base
from pymodaq.daq_move.utility_classes import comon_parameters
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo
from easydict import EasyDict as edict

from pymodaq_plugins.hardware.PI.mmc_wrapper import MMC_Wrapper

#is64bit = sys.maxsize > 2**32
if (sys.maxsize > 2**32):
    raise Exception("It must a python 32 bit version")

ports = MMC_Wrapper.ports

class DAQ_Move_PI_MMC(DAQ_Move_base):
    """
        Wrapper object to access the Physik Instrumente fonctionnalities, similar wrapper for all controllers.

        =============== =======================
        **Attributes**   **Type**
        *GCS_path*       string
        *gcs_device*     string
        *devices*        instance of GCSDevice
        *params*         dictionnary list
        =============== =======================

        See Also
        --------
        daq_utils.ThreadCommand
    """

    _controller_units = 'mm'  # dependent on the stage type so to be updated accordingly using self.controller_units = new_unit

    com_ports = MMC_Wrapper.aliases
    controller_addresses = []
    is_multiaxes=False
    stage_names=[]

    params= [{'title': 'COM Ports:', 'name': 'com_port', 'type': 'list', 'values': com_ports},
           {'title': 'Controller_address:', 'name': 'controller_address', 'type': 'list', 'values': controller_addresses},
           {'title': 'Stages:', 'name': 'stage', 'type': 'list', 'values': list(MMC_Wrapper.stages.keys())},
           {'title': 'Closed loop?:', 'name': 'closed_loop', 'type': 'bool', 'value': True},
           {'title': 'Controller ID:', 'name': 'controller_id', 'type': 'str', 'value': '', 'readonly': True},
           {'title': 'MultiAxes:', 'name': 'multiaxes', 'type': 'group','visible':is_multiaxes, 'children':[
                    {'title': 'is Multiaxes:', 'name': 'ismultiaxes', 'type': 'bool', 'value': is_multiaxes, 'default': False},
                    {'title': 'Status:', 'name': 'multi_status', 'type': 'list', 'value': 'Master', 'values': ['Master','Slave']},
                    {'title': 'Axis:', 'name': 'axis', 'type': 'list',  'values':stage_names},

                    ]}]+comon_parameters





    def __init__(self,parent=None,params_state=None):

        super().__init__(parent,params_state)
        self.settings.child(('epsilon')).setValue(0.01)



    def commit_settings(self,param):
        """
            | Activate any parameter changes on the PI_GCS2 hardware.
            |
            | Called after a param_tree_changed signal from DAQ_Move_main.

            =============== ================================ ========================
            **Parameters**  **Type**                          **Description**
            *param*         instance of pyqtgraph Parameter  The parameter to update
            =============== ================================ ========================

            See Also
            --------
            daq_utils.ThreadCommand, DAQ_Move_PI.enumerate_devices
        """
        try:
            if param.name() == 'stage':
                self.controller.stage = param.value()

            elif param.name() == 'controller_address':
                self.controller.MMC_select(param.value())
                self.check_position()


        except Exception as e:
            self.emit_status(ThreadCommand("Update_Status", [getLineInfo()+ str(e), 'log']))


    def enumerate_devices(self):
        """
        """
        try:
            devices = self.controller.MMC_initNetwork(3) #up to 3 controller in a row (could be 16 at max but useless)
            self.settings.child('controller_address').setOpts(limits=devices)
            return devices
        except Exception as e:
            self.emit_status(ThreadCommand("Update_Status",[getLineInfo()+ str(e),'log']))

    def ini_stage(self,controller=None):
        """
            Initialize the controller and stages (axes) with given parameters.
            See Also
            --------
            DAQ_Move_PI.set_referencing, daq_utils.ThreadCommand
        """

        try:
            device=""
            # initialize the stage and its controller status
            # controller is an object that may be passed to other instances of DAQ_Move_Mock in case
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
                self.controller = MMC_Wrapper(com_port=self.settings.child('com_port').value())
                self.controller.open()
                devices = self.enumerate_devices()
                self.controller.MMC_select(devices[0])

            self.check_position()

            self.status.controller=self.controller
            self.status.info=""
            self.status.controller=self.controller
            self.status.initialized=True
            return self.status


        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status',[getLineInfo()+ str(e),'log']))
            self.status.info=getLineInfo()+ str(e)
            self.status.initialized=False
            return self.status


    def close(self):
        """
            close the current instance of PI_GCS2 instrument.
        """
        self.controller.MMC_COM_close()

    def stop_motion(self):
        """
            See Also
            --------
            DAQ_Move_base.move_done
        """
        self.controller.MMC_globalBreak()
        self.move_done()

    def check_position(self):
        """
            Get the current hardware position with scaling conversion of the PI_GCS2 instrument provided by get_position_with_scaling

            See Also
            --------
            DAQ_Move_base.get_position_with_scaling, daq_utils.ThreadCommand
        """
        pos = self.controller.getPos()
        pos=self.get_position_with_scaling(pos)
        self.current_position = pos
        self.emit_status(ThreadCommand('check_position',[pos]))
        return pos

    def move_Abs(self,position):
        """
        """

        position=self.check_bound(position)
        self.target_position=position

        position=self.set_position_with_scaling(position)
        out=self.controller.moveAbs(self.settings.child('controller_address').value(), position)

        self.poll_moving()


    def move_Rel(self,position):
        """
            Make the hardware relative move of the PI_GCS2 instrument from the given position after thread command signal was received in DAQ_Move_main.

            =============== ========= =======================
            **Parameters**  **Type**   **Description**

            *position*       float     The absolute position
            =============== ========= =======================

            See Also
            --------
            DAQ_Move_base.set_position_with_scaling, DAQ_Move_PI.set_referencing, DAQ_Move_base.poll_moving

        """
        position=self.check_bound(self.current_position+position)-self.current_position
        self.target_position=position+self.current_position
        position = self.set_position_relative_with_scaling(position)

        out=self.controller.moveRel(self.settings.child('controller_address').value(), position)
        self.poll_moving()

    def move_Home(self):
        """

            See Also
            --------
            DAQ_Move_PI.set_referencing, DAQ_Move_base.poll_moving
        """
        self.controller.find_home()
        moving = True
        pos = self.check_position()
        while moving:
            pos_tmp = self.check_position()
            moving = abs(pos - pos_tmp) > 0.001
            QThread.msleep(100)
            pos = pos_tmp
        self.controller.MMC_sendCommand('DH')  #to define it as home
        QThread.msleep(500)
        self.check_position()


