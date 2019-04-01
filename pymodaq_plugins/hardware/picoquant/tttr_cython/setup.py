# -*- coding: utf-8 -*-

from distutils.core import setup
from Cython.Build import cythonize
import numpy

setup(
  name = 'TTTR',
  ext_modules = cythonize("tttr.pyx"),
  include_dirs=[numpy.get_include()]
)