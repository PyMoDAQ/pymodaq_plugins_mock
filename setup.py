from plugin_info import SHORT_PLUGIN_NAME, packages_required, package_url, author_email, author, description
PLUGIN_NAME = f'pymodaq_plugins_{SHORT_PLUGIN_NAME}'

import importlib
import sys
try:
    import setuptools
    from setuptools import setup, find_packages
    from setuptools.command import install
except ImportError:
    sys.stderr.write("Warning: could not import setuptools; falling back to distutils.\n")
    from distutils.core import setup
    from distutils.command import install

version = importlib.import_module('.version', PLUGIN_NAME)

with open('README.rst') as fd:
    long_description = fd.read()

setupOpts = dict(
    name=PLUGIN_NAME,
    description=description,
    long_description=long_description,
    license='CECILL B',
    url=package_url,
    author=author,
    author_email=author_email,
    classifiers=[
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
    ], )


setup(
    version=version.get_version(),
    packages=find_packages(),
    package_data={'': ['*.dll']},
    entry_points={'pymodaq.plugins': f'default = {PLUGIN_NAME}'},
    install_requires=[
        'pymodaq>=2.0',
        ]+packages_required,
    **setupOpts
)

