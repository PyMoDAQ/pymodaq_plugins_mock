"""
Demo Wrapper to illustrate the plugin developpement. This Mock wrapper will emulate communication with an instrument
"""

from time import perf_counter, sleep
import math
from numpy import random

ports = ['COM1', 'COM2']


class ActuatorWrapper:
    units = 'mm'

    def __init__(self):
        self._com_port = ''
        self._current_value = 0
        self._target_value = None

    def open_communication(self):
        """
        fake instrument opening communication.
        Returns
        -------
        bool: True is instrument is opened else False
        """
        return True

    def move_at(self, value):
        """
        Send a call to the actuator to move at the given value
        Parameters
        ----------
        value: (float) the target value
        """
        self._target_value = value
        self._current_value = value

    def stop(self):
        pass

    def get_value(self):
        """
        Get the current actuator value
        Returns
        -------
        float: The current value
        """
        return self._current_value

    def close_communication(self):
        pass


class ActuatorWrapperWithTau(ActuatorWrapper):

    units = '°'

    def __init__(self):
        super().__init__()
        self._epsilon = 1e-2
        self._tau = 3  # s
        self._alpha = None
        self._init_value = 0.
        self._current_value = 0.
        self._start_time = 0
        self._moving = False

    @property
    def epsilon(self):
        return self._epsilon

    @epsilon.setter
    def epsilon(self, eps):
        self._epsilon = eps

    @property
    def is_moving(self):
        return self._moving

    @property
    def tau(self):
        """
        fetch the characteristic decay time in s
        Returns
        -------
        float: the current characteristic decay time value

        """
        return self._tau

    @tau.setter
    def tau(self, value):
        """
        Set the characteristic decay time value in s
        Parameters
        ----------
        value: (float) a strictly positive characteristic decay time
        """
        if value <= 0:
            raise ValueError(f'A characteristic decay time of {value} is not possible. It should be strictly positive')
        else:
            self._tau = value

    def move_at(self, value):
        """
        Send a call to the actuator to move at the given value
        Parameters
        ----------
        value: (float) the target value
        """
        self._target_value = value
        self._init_value = self._current_value
        if self._init_value != self._target_value:
            self._alpha = math.fabs(math.log(self._epsilon / math.fabs(self._init_value - self._target_value)))
        else:
            self._alpha = math.fabs(math.log(self._epsilon / 10))
        self._start_time = perf_counter()
        self._moving = True

    def stop(self):
        self._moving = False

    def get_value(self):
        """
        Get the current actuator value
        Returns
        -------
        float: The current value
        """
        if self._moving:
            curr_time = perf_counter()
            self._current_value = \
                math.exp(- self._alpha * (curr_time-self._start_time) / self._tau) *\
                (self._init_value - self._target_value) + self._target_value

        self._current_value += (random.random() - 0.5) * self.epsilon / 10
        # add some small random value to get fluctuations in positions

        return self._current_value


class ActuatorWrapperWithTauMultiAxes(ActuatorWrapper):

    axes = ['X', 'Y', 'Theta']
    _units = ['mm', 'mm', '°']
    _epsilon = 0.01

    def __init__(self):
        super().__init__()
        self._tau = 0.5  # s
        self._alpha = None
        self._as_group = False
        self._grouped_axes = []

        self._target_values = [0.0 for _ in self.axes]
        self._current_values = [0.0 for _ in self.axes]

        self._init_values = [0.0 for _ in self.axes]

        self._current_value = 0.

        self._start_times = [0. for _ in self.axes]
        self._moving = [False for _ in self.axes]

    def _get_index_from_name(self, axis: str):
        return self.axes.index(axis)

    def get_units(self, axis: str):
        return self._units[self._get_index_from_name(axis)]

    @property
    def epsilon(self) -> float:
        return self._epsilon

    @epsilon.setter
    def epsilon(self, eps: float):
        self._epsilon = eps

    def is_moving(self, axis: str):
        return self._moving[self._get_index_from_name(axis)]

    @property
    def tau(self):
        """
        fetch the characteristic decay time in s
        Returns
        -------
        float: the current characteristic decay time value

        """
        return self._tau

    @tau.setter
    def tau(self, value):
        """
        Set the characteristic decay time value in s
        Parameters
        ----------
        value: (float) a strictly positive characteristic decay time
        """
        if value <= 0:
            raise ValueError(f'A characteristic decay time of {value} is not possible. It should be strictly positive')
        else:
            self._tau = value

    def move_as_group(self, as_group: bool, grouped_axes: list = []):
        self._as_group = as_group
        self._grouped_axes = grouped_axes
        self._grouped_axes_set = [False for _ in grouped_axes]

    def move_at(self, value: float, axis: str):
        """
        Send a call to the actuator to move at the given value
        Parameters
        ----------
        value: (float) the target value
        """
        if self._as_group:
            self._grouped_axes_set[self._grouped_axes.index(axis)] = True
        self._moving[self._get_index_from_name(axis)] = False

        self._target_values[self._get_index_from_name(axis)] = value
        self._init_values[self._get_index_from_name(axis)] = self._current_values[self._get_index_from_name(axis)]
        if self._init_values[self._get_index_from_name(axis)] != self._target_values[self._get_index_from_name(axis)]:
            self._alpha = math.fabs(math.log(self._epsilon /
            math.fabs(self._init_values[self._get_index_from_name(axis)] -
                      self._target_values[self._get_index_from_name(axis)])))
        else:
            self._alpha = math.fabs(math.log(self._epsilon / 10))

        if not self._as_group:
            self._start_times[self._get_index_from_name(axis)] = perf_counter()
            self._moving[self._get_index_from_name(axis)] = True
        elif all(self._grouped_axes_set):
            start = perf_counter()
            for ind in range(len(self.axes)):
                self._start_times[ind] = start
                self._moving[ind] = True
                self._grouped_axes_set[ind] = False

    def stop(self, axis: str):
        self._moving[self._get_index_from_name(axis)] = False

    def get_value(self, axis: str):
        """
        Get the current actuator value
        Returns
        -------
        float: The current value
        """
        if self._moving[self._get_index_from_name(axis)]:
            curr_time = perf_counter()
            self._current_values[self._get_index_from_name(axis)] = \
                math.exp(- self._alpha * (curr_time-self._start_times[self._get_index_from_name(axis)]) / self._tau) *\
                (self._init_values[self._get_index_from_name(axis)] - self._target_values[self._get_index_from_name(axis)]) +\
                self._target_values[self._get_index_from_name(axis)]

        self._current_values[self._get_index_from_name(axis)] += (random.random() - 0.5) * self.epsilon / 10
        # add some small random value to get fluctuations in positions

        return self._current_values[self._get_index_from_name(axis)]



if __name__ == '__main__':
    actuator = ActuatorWrapperWithTau()
    init_pos = actuator.get_value()
    print(f'Init: {init_pos}')
    target = 100
    actuator.move_at(target)
    time = perf_counter()
    while perf_counter() - time < 100:
        sleep(0.1)
        pos = actuator.get_value()
        print(pos)
        if math.fabs(pos - target) < actuator.epsilon:
            print(f'Elapsed time : {perf_counter() - time}')
            break

