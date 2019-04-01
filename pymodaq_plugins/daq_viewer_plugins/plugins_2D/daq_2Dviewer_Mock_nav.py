from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSlot
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base
import numpy as np
from easydict import EasyDict as edict
from collections import OrderedDict
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo, ScanParameters
from pymodaq.daq_utils.daq_utils import gauss1D
from pymodaq.daq_viewer.utility_classes import comon_parameters

class DAQ_2DViewer_Mock_nav(DAQ_Viewer_base):
    """
        ==================== ==================
        **Atrributes**        **Type**
        *params*              dictionnary list
        *hardware_averaging*  boolean
        *x_axis*              1D numpy array      
        *ind_data*            int
        ==================== ==================

        See Also
        --------

        utility_classes.DAQ_Viewer_base
    """
    params= comon_parameters+[
             {'title': 'Show Navigator:', 'name': 'show_navigator', 'type': 'bool', 'value': False},
             {'name': 'rolling', 'type': 'int', 'value': 0, 'min':0},
             {'name': 'Mock1', 'type': 'group', 'children':[
                {'name': 'Npts', 'type': 'int', 'value': 200 , 'default':200, 'min':10},
                {'name': 'Amp', 'type': 'int', 'value': 20 , 'default':20, 'min':1},
                {'name': 'x0', 'type': 'float', 'value': 50 , 'default':50, 'min':0},
                {'name': 'dx', 'type': 'float', 'value': 20 , 'default':20, 'min':1},
                {'name': 'n', 'type': 'float', 'value': 1 , 'default':1, 'min':1},
                {'name': 'amp_noise', 'type': 'float', 'value': 0.1 , 'default':0.1, 'min':0}
                ]},
                ]
    hardware_averaging=False

    def __init__(self,parent=None,params_state=None): #init_params is a list of tuple where each tuple contains info on a 1D channel (Ntps,amplitude, width, position and noise)
        super(DAQ_2DViewer_Mock_nav,self).__init__(parent,params_state)


        self.x_axis=None
        self.y_axis = None
        self.signal_axis = None
        self.ind_data=0
        self.data = None

        self.scan_parameters = None

    def commit_settings(self,param):
        """
            Setting the mock data

            ============== ========= =================
            **Parameters**  **Type**  **Description**
            *param*         none      not used
            ============== ========= =================

            See Also
            --------
            set_Mock_data
        """
        if param.name() == 'show_navigator':
            self.emit_status(ThreadCommand('show_navigator'))
            param.setValue(False)
        else:
            self.set_Mock_data()
               
                
    def set_Mock_data(self):
        """
            For each parameter of the settings tree :
                * compute linspace numpy distribution with local parameters values
                * shift right the current data of ind_data position
                * add computed results to the data_mock list 

            Returns
            -------
            list
                The computed data_mock list.
        """

        param = self.settings.child('Mock1')  #the first one is ROIselect only valid in the 2D case

        self.signal_axis=np.linspace(0,param.children()[0].value()-1,param.children()[0].value())
        data_tmp=param.children()[1].value()*gauss1D(self.signal_axis,param.children()[2].value(),param.children()[3].value(),param.children()[4].value())

        data_tmp = data_tmp * np.sin(self.signal_axis / 4) ** 2
        data_tmp+=param.children()[5].value()*np.random.rand((param.children()[0].value()))
        data_tmp=np.roll(data_tmp,self.ind_data*self.settings.child(('rolling')).value())
        self.data_mock = data_tmp
        self.ind_data+=1
        return self.data_mock

    def ini_detector(self, controller=None):
        """
            Initialisation procedure of the detector updating the status dictionnary.

            See Also
            --------
            set_Mock_data, daq_utils.ThreadCommand
        """
        self.status.update(edict(initialized=False,info="",x_axis=None,y_axis=None,controller=None))
        try:

            if self.settings.child(('controller_status')).value()=="Slave":
                if controller is None: 
                    raise Exception('no controller has been defined externally while this detector is a slave one')
                else:
                    self.controller=controller
            else:
                self.controller="Mock controller"



            self.set_Mock_data()

            x_axis = np.linspace(0, 10, 11)
            y_axis = np.linspace(0, 10, 11)

            self.data = np.zeros((len(x_axis), len(y_axis), len(self.signal_axis)))
            #self.data_ptr = self.data.ctypes.data_as()

            # initialize viewers with the future type of data
            self.data_grabed_signal_temp.emit([OrderedDict(name='Mock1', nav_axes=[0, 1] ,
                                data=self.data, type='DataND',
                nav_x_axis= x_axis, nav_y_axis= y_axis, labels=['Mock1'],
                                               x_axis = self.signal_axis)])

            QtWidgets.QApplication.processEvents()

            self.emit_status(ThreadCommand('show_scanner'))
            self.status.initialized=True
            self.status.controller=self.controller
            self.status.x_axis = self.x_axis
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status',[getLineInfo()+ str(e),'log']))
            self.status.info=getLineInfo()+ str(e)
            self.status.initialized=False
            return self.status

    def close(self):
        """
            Not implemented.
        """
        pass

    @pyqtSlot(ScanParameters)
    def update_scanner(self, scan_parameters):
        self.scan_parameters = scan_parameters
        self.x_axis = self.scan_parameters.axis_2D_1
        self.y_axis = self.scan_parameters.axis_2D_2
        self.prepare_moves()

    def prepare_moves(self):
        """
        prepare given actuators with positions from scan_parameters
        Returns
        -------

        """
        pass

    def get_xaxis(self):
        """
        """
        return self.scan_parameters.axis_2D_1

    def get_yaxis(self):
        """
        """
        return self.scan_parameters.axis_2D_2

    def grab_data(self, Naverage=1, **kwargs):
        """

        """
        # start moves
        self.data = np.zeros((len(self.x_axis), len(self.y_axis), len(self.signal_axis)))
        self.data_grabed_signal_temp.emit([OrderedDict(name='Mock1', nav_axes=[0, 1],
                                                       data=self.data, type='DataND',
                                                       nav_x_axis=self.x_axis, nav_y_axis=self.y_axis, labels=['Mock1'],
                                                       x_axis=self.signal_axis)])
        QtWidgets.QApplication.processEvents()

        for ind, (xpos, ypos) in enumerate(self.scan_parameters.positions):

            self.data[self.scan_parameters.axis_2D_1_indexes[ind], self.scan_parameters.axis_2D_2_indexes[ind], :] = self.set_Mock_data()
            if ind%10 == 0:
                self.data_grabed_signal_temp.emit([OrderedDict(name='Mock1', nav_axes=[0, 1],
                                                               data=self.data, type='DataND',
                                                       nav_x_axis=self.x_axis, nav_y_axis=self.y_axis, labels=['Mock1'],
                                                       x_axis=self.signal_axis)])
                QtWidgets.QApplication.processEvents()
            QThread.msleep(100)

        self.data_grabed_signal.emit([OrderedDict(name='Mock1', nav_axes=[0, 1],
                                                       data=self.data, type='DataND',
                                                       nav_x_axis=self.x_axis, nav_y_axis=self.y_axis, labels=['Mock1'],
                                                       x_axis=self.signal_axis)])

    def stop(self):
        """
            not implemented.
        """
        
        return ""
