# -*- coding: utf-8 -*-
"""
Created the 24/10/2022

@author: Sebastien Weber
"""
import numpy as np
import pymodaq.utils.math_utils as mutils


class MultiAxis:
    axes_indexes = [0, 1, 2]

    def __init__(self):
        super().__init__()
        self._image = None
        self._current_value = [0., 0., 0.]

    def get_value(self, axis: int = 0):
        return self._current_value[self.axes_indexes.index(axis)]

    def set_value(self, axis: int = 0, value: float = 0.):
        self._current_value[self.axes_indexes.index(axis)] = value

