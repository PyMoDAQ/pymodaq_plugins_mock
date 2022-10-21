PyMoDAQ Plugins
###############

.. image:: https://img.shields.io/pypi/v/pymodaq_plugins.svg
   :target: https://pypi.org/project/pymodaq_plugins/
   :alt: Latest Version

.. image:: https://readthedocs.org/projects/pymodaq/badge/?version=latest
   :target: https://pymodaq.readthedocs.io/en/stable/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/PyMoDAQ/pymodaq_plugins/workflows/Upload%20Python%20Package/badge.svg
    :target: https://github.com/PyMoDAQ/pymodaq_plugins

Plugins initially developed with PyMoDAQ. Includes Mock plugins that are plugins of virtual instruments dedicated
to code testing for new functionalities or development.


Authors
=======

* Sebastien J. Weber

Instruments
===========
Below is the list of instruments included in this plugin

Actuators
+++++++++

* **Mock** actuator to test PyMoDAQ functionnalities
* **MockTau** mock actuator with caracteristic time to reach set value
* **TCP server** to communicate with other DAQ_Move or third party applications

Viewer0D
++++++++

* **Mock 0D** detector to test PyMoDAQ functionnalities
* **Mock Adaptive** detector to test PyMoDAQ adaptive scan mode
* **TCP server** to communicate with other DAQ_Viewer or third party applications

Viewer1D
++++++++

* **Mock 1D** detector to test PyMoDAQ functionnalities
* **Mock Spectro** detector to test pymodaq_spectro functionalities
* **TCP server** to communicate with other DAQ_Viewer or third party applications

Viewer2D
++++++++

* **Mock 2D** detector to test PyMoDAQ functionnalities
* **TCP server** to communicate with other DAQ_Viewer or third party applications

ViewerND
++++++++

* **Mock ND** detector to test PyMoDAQ functionnalities
