from typing import List

import numpy as np
from scipy.ndimage import center_of_mass

from pymodaq.utils.data import DataToExport, DataActuator, DataCalculated
from pymodaq.extensions.pid.utils import PIDModelGeneric, DataToActuatorPID, main


class PIDModelBeamSteering(PIDModelGeneric):
    limits = dict(max=dict(state=False, value=100),
                  min=dict(state=False, value=-100),)
    konstants = dict(kp=0.1, ki=0.000, kd=0.0000)

    setpoint_ini = [128., 128.]
    setpoints_names = ['Xaxis', 'Yaxis']

    actuators_name = ["Xpiezo", "Ypiezo"]
    detectors_name = ['Camera']

    Nsetpoints = 2
    params = [{'title': 'Threshold', 'name': 'threshold', 'type': 'float', 'value': 10.}]

    def __init__(self, pid_controller):
        super().__init__(pid_controller)

    def update_settings(self, param):
        """
        Get a parameter instance whose value has been modified by a user on the UI
        Parameters
        ----------
        param: (Parameter) instance of Parameter object
        """
        if param.name() == '':
            pass

    def ini_model(self):
        super().ini_model()

    def convert_input(self, measurements: DataToExport) -> DataToExport:
        """
        Convert the measurements in the units to be fed to the PID (same dimensionality as the setpoint)
        Parameters
        ----------
        measurements: DataToExport
         DataToExport object from which the model extract a value of the same units as the setpoint

        Returns
        -------
        DataToExport: the converted input as 0D DataCalculated stored in a DataToExport
        """
        image = measurements.get_data_from_dim('Data2D')[0][0]
        image = image - self.settings['threshold']
        image[image < 0] = 0
        x, y = center_of_mass(image)
        self.curr_input = [y, x]
        return DataToExport('inputs',
                            data=[DataCalculated(self.setpoints_names[ind],
                                                 data=[np.array([self.curr_input[ind]])])
                                  for ind in range(len(self.curr_input))])

    def convert_output(self, outputs: List[float], dt, stab=True) -> DataToActuatorPID:
        """
        Convert the output of the PID in units to be fed into the actuator
        Parameters
        ----------
        outputs: (list of float) output value from the PID from which the model extract a value of the same units as the actuator
        dt: (float) elapsed time in seconds since last call
        Returns
        -------
        DataToActuatorPID: the converted output as a DataToActuatorPID object (derived from DataToExport)

        """
        #print('output converted')
        
        self.curr_output = outputs
        return DataToActuatorPID('pid', mode='rel',
                                 data=[DataActuator(self.actuators_name[ind], data=outputs[ind])
                                       for ind in range(len(outputs))])


if __name__ == '__main__':
    main("beam_steering_mock.xml")


