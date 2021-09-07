import numpy as np
from pymodaq.daq_utils.daq_utils import gauss2D

class PIDMock:

    Nactuators = 2
    axis = ['H', 'V']
    Nx = 256
    Ny = 256

    def __init__(self, positions=None, wh=(40, 50), noise=0.1, amp=10):
        super().__init__()
        if positions is None:
            self.current_positions = dict(zip(self.axis, [128. for ind in range(self.Nactuators)]))
        else:
            assert isinstance(positions, list)
            assert len(positions) == self.Nactuators
            self.current_positions = positions

        self.amp = amp
        self.noise = noise
        self.wh = wh


    def check_position(self, axis):
        return self.current_positions[axis]

    def move_abs(self, position, axis):
        self.current_positions[axis] = position

    def get_xaxis(self):
        return np.linspace(0, self.Nx, self.Nx, endpoint=False)

    def get_yaxis(self):
        return np.linspace(0, self.Ny, self.Ny, endpoint=False)

    def set_Mock_data(self):
        """
        """
        x_axis = self.get_xaxis()
        y_axis = self.get_yaxis()

        data_mock = self.amp * gauss2D(x_axis, self.current_positions['H'], self.wh[0],
                                       y_axis, self.current_positions['V'], self.wh[1], 1) + \
                    self.noise * np.random.rand(len(y_axis), len(x_axis))

        return data_mock
