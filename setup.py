import distutils.dir_util
from distutils.command import build
import os, sys, re
try:
    import setuptools
    from setuptools import setup, find_packages
    from setuptools.command import install
except ImportError:
    sys.stderr.write("Warning: could not import setuptools; falling back to distutils.\n")
    from distutils.core import setup
    from distutils.command import install

from pymodaq_plugins.version import get_version

with open('README.rst') as fd:
    long_description = fd.read()

setupOpts = dict(
    name='pymodaq_plugins',
    description='Hardware plugins for PyMoDAQ',
    long_description=long_description,
    license='MIT',
    url='http://pymodaq.cnrs.fr',
    author='Sébastien Weber',
    author_email='sebastien.weber@cemes.fr',
    classifiers = [
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Other Environment",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: Scientific/Engineering :: Visualization",
        "License :: CeCILL-B Free Software License Agreement (CECILL-B)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
        ],)

def listAllPackages(pkgroot):
    path = os.getcwd()
    n = len(path.split(os.path.sep))
    subdirs = [i[0].split(os.path.sep)[n:] for i in os.walk(os.path.join(path, pkgroot)) if '__init__.py' in i[2]]
    return ['.'.join(p) for p in subdirs]


allPackages = (listAllPackages(pkgroot='pymodaq_plugins')) #+
               #['pyqtgraph.'+x for x in helpers.listAllPackages(pkgroot='examples')])



def get_packages():

    packages=find_packages()
    for pkg in packages:
        if 'hardware.' in pkg:
            packages.pop(packages.index(pkg))
    return packages

allPackages = get_packages()

hardware_path=os.path.join('pymodaq_plugins','hardware')

def get_hardware_packages(base_dir='',packages={}):
    for pack in os.scandir(base_dir):
        if pack.is_dir():
            if '__pycache__' != pack.name:
                packages.update({os.path.relpath(pack.path,'pymodaq_plugins'): '*.*'})
                get_hardware_packages(pack.path,packages)
    return packages

packages_data=dict([])
get_hardware_packages(hardware_path,packages_data)

setup(
    version=get_version(),
     #cmdclass={'build': Build,},
    #           'install': Install,
    #           'deb': helpers.DebCommand,
    #           'test': helpers.TestCommand,
    #           'debug': helpers.DebugCommand,
    #           'mergetest': helpers.MergeTestCommand,
    #           'style': helpers.StyleCommand},
    packages=find_packages(),
    package_data={'': ['*.dll']},
    install_requires = [],
    **setupOpts
)

