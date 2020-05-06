from PyQt5 import QtWidgets
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base
import numpy as np
from collections import OrderedDict
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo, DataFromPlugins, Axis
import sys
import clr
from easydict import EasyDict as edict
from pymodaq.daq_viewer.utility_classes import comon_parameters




class DAQ_1DViewer_OceanOptics(DAQ_Viewer_base):
    """PyMoDAQ plugin controlling spectrometers from OceanOptics and using their OmniDriver wrapper ('NETOmniDriver-NET40')
    The wrapper is interfaced using the clr package and then importing Omnidriver as a standart python package
    https://oceanoptics.com/api/omnidriver/index.html?overview-summary.html
    >>>clr.AddReference("NETOmniDriver-NET40")
    >>>import OmniDriver as omnidriver
    The plugin enables the discovery of any connected usb spectrometers and can control them in parallel. It extracts the
    calibrated wavelength and will export datas that will be plotted with respect to this wavelengths vector.

    Used methods from the wrapper:
    ------------------------------
     setIntegrationTime
     getIntegrationTime

    See Also
    --------
    utility_classes.DAQ_Viewer_base
    """
    omnidriver_path='C:\\Program Files\\Ocean Optics\\OmniDriver\\OOI_HOME'
    try:
        sys.path.append(omnidriver_path)
        clr.AddReference("NETOmniDriver-NET40")
        import OmniDriver as omnidriver

    except:
        omnidriver =None

    params=comon_parameters+ [{'title': 'Omnidriver path:', 'name': 'omnidriver_path', 'type': 'browsepath', 'value': omnidriver_path},
            {'title': 'N spectrometers:','name': 'Nspectrometers', 'type': 'int', 'value': 0 , 'default':0, 'min':0},
             {'title': 'Spectrometers:','name': 'spectrometers', 'type': 'group', 'children': []},
            ]

    hardware_averaging=True


    def __init__(self,parent=None,params_state=None): #init_params is a list of tuple where each tuple contains info on a 1D channel (Ntps,amplitude, width, position and noise)
        super(DAQ_1DViewer_OceanOptics,self).__init__(parent,params_state)


        self.controller=None
        self.spectro_names = [] #contains the spectro name as returned from the wrapper
        self.spectro_id = [] # contains the spectro id as set by the ini_detector method and equal to the Parameter name

    def commit_settings(self,param):
        """

        """
        if param.name()=='exposure_time':
            ind_spectro=self.spectro_id.index(param.parent().name())
            self.controller.setIntegrationTime(ind_spectro,param.value()*1000)

            param.setValue(self.controller.getIntegrationTime(ind_spectro)/1000)


        elif param.name()=='omnidriver_path':
            try:
                sys.path.append(param.value())
                clr.AddReference("NETOmniDriver-NET40")
                import OmniDriver
                self.omnidriver=OmniDriver
            except:
                pass
                


    def ini_detector(self, controller=None):
        """
            Initialisation procedure of the detector updating the status dictionnary.

            See Also
            --------
            set_Mock_data, daq_utils.ThreadCommand
        """
        self.status.update(edict(initialized=False,info="",x_axis=None,y_axis=None,controller=None))
        try:
            #open spectro, check and set spectro connected, check and set min max exposure

            if self.settings.child(('controller_status')).value()=="Slave":
                if controller is None: 
                    raise Exception('no controller has been defined externally while this detector is a slave one')
                else:
                    self.controller=controller
            else:
                self.controller=self.omnidriver.NETWrapper()

            N=self.controller.openAllSpectrometers()
            self.settings.child('Nspectrometers').setValue(N)
            self.spectro_names=[]
            self.spectro_id = []
            data_init=[]
            for ind_spectro in range(N):
                name=self.controller.getName(ind_spectro)
                self.spectro_names.append(name)
                self.spectro_id.append('spectro{:d}'.format(ind_spectro))

                exp_max=self.controller.getMaximumIntegrationTime(ind_spectro)
                exp_min=self.controller.getMinimumIntegrationTime(ind_spectro)
                exp=self.controller.getIntegrationTime(ind_spectro)/1000
                wavelengths = self.get_xaxis(ind_spectro)
                data_init.append(DataFromPlugins(name=name, data=[np.zeros_like(wavelengths)], dim='Data1D',
                                                 x_axis=Axis(data=wavelengths, label='Wavelength', units='nm')))
                for ind in range(2): #this is to take into account that adding it once doen't work (see pyqtgraph Parameter...)
                    try:
                        self.settings.child(('spectrometers')).addChild({'title': name,'name': 'spectro{:d}'.format(ind_spectro), 'type': 'group', 'children':[
                            {'title': 'grab spectrum:','name': 'grab', 'type': 'bool', 'value': True},
                            {'title': 'Exposure time (ms):','name': 'exposure_time', 'type': 'int', 'value': int(exp), 'min': int(exp_min/1000), 'max': int(exp_max/1000)},
                            ]
                            })
                    except:
                        pass


                QtWidgets.QApplication.processEvents()
            #init viewers
            if N == 0:
                raise Exception('No detected hardware')
            self.data_grabed_signal_temp.emit(data_init)

            self.status.initialized=True
            self.status.controller=self.controller
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status',[getLineInfo()+ str(e),'log']))
            self.status.info=getLineInfo()+ str(e)
            self.status.initialized=False
            return self.status

    def get_xaxis(self,ind_spectro):
        wavelengths_chelou = self.controller.getWavelengths(ind_spectro)
        wavelengths = np.array([wavelengths_chelou[ind] for ind in range(len(wavelengths_chelou))])

        return wavelengths

    def close(self):
        """
            Not implemented.
        """
        self.controller.closeAllSpectrometers()


    def grab_data(self, Naverage=1, **kwargs):
        """

        """
        try:
            datas=[]
            for ind_spectro in range(len(self.spectro_names)):
                if self.settings.child('spectrometers','spectro{:d}'.format(ind_spectro),'grab').value():
                    self.controller.setScansToAverage(ind_spectro,Naverage)
                    data_chelou=self.controller.getSpectrum(ind_spectro)
                    data=np.array([data_chelou[ind] for ind in range(len(data_chelou))])
                    datas.append(DataFromPlugins(name=self.spectro_names[ind_spectro],data=[data], dim='Data1D'))
                    QtWidgets.QApplication.processEvents()

            self.data_grabed_signal.emit(datas)

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status',[getLineInfo()+ str(e),"log"]))

    def stop(self):
        """

        """
        for ind_spec, name in enumerate(self.spectro_names):
            self.controller.stopAveraging(ind_spec)
