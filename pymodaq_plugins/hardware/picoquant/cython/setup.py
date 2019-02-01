from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

setup(
    ext_modules = cythonize([
        Extension("th260lib", ["th260lib.pyx"],
                libraries=["th260lib64"])
                  ])
)