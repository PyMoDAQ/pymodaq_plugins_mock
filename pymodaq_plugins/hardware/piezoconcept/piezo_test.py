from pymodaq_plugins.hardware.piezoconcept.piezoconcept import PiezoConcept, Position, Time
import numpy as np

if __name__ == '__main__':

    controller = PiezoConcept()
    controller.init_communication('COM6')
    print(controller.get_controller_infos())
    controller.get_time_interval()
    xaxis = np.linspace(100000, 120000, 21)
    yaxis = np.linspace(100000, 110000, 11)
    zaxis = np.linspace(0, 0, 11)

    #controller.set_positions_simple(xaxis, yaxis, [])
    #controller.run_simple()
    #controller._get_read()
    xaxis = np.linspace(100000, 120000, 21)
    yaxis = np.linspace(100000, 110000, 21)
    #controller.set_positions_arbitrary([xaxis, yaxis])
    #controller.run_arbitrary()
    #controller._get_read()
    controller.get_TTL_state(1)
    controller._get_read()
    pass