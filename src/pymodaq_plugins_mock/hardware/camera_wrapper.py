# -*- coding: utf-8 -*-
"""
Created the 24/10/2022

@author: Sebastien Weber
"""
import numpy as np
import pymodaq.daq_utils.math_utils as mylib


class Camera:
    Nx = 256
    Ny = 256
    amp = 20
    x0 = 128
    y0 = 128
    dx = 20
    dy = 40
    n = 1
    amp_noise = 4
    fringes = True
    axes = ['X', 'Y', 'Theta']

    def __init__(self):
        super().__init__()
        self._image = None
        self._current_value = dict(X=0., Y=0., Theta=0.)
        self.base_Mock_data()

    def get_value(self, axis: str):
        return self._current_value[axis]

    def set_value(self, axis:str = 'X', value: float = 0.):
        self._current_value[axis] = value
        if axis == 'Theta':
            self.base_Mock_data()

    def base_Mock_data(self):
        self.x_axis = np.linspace(0, self.Nx, self.Nx, endpoint=False)
        self.y_axis = np.linspace(0, self.Ny, self.Ny, endpoint=False)
        data_mock = self.amp * (
            mylib.gauss2D(self.x_axis, self.x0, self.dx,
                          self.y_axis, self.y0, self.dy,
                          self.n,
                          angle=self._current_value['Theta']))

        for indy in range(data_mock.shape[0]):
            if self.fringes:
                data_mock[indy, :] = data_mock[indy, :] * np.sin(self.x_axis / 4) ** 2

        self._image = data_mock
        return self._image

    def get_data(self):
        return np.roll(np.roll(self._image + self.amp_noise * np.random.rand(len(self.y_axis),
                                                                             len(self.x_axis)),
                               int(self._current_value['X']), axis=1),
                       int(self._current_value['Y']), axis=0)
