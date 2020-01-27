:orphan:

=========
Changelog
=========
* :release:`1.3.0 <2020-01-27>`
* :feature:`0` Added new DAQ_Viewer1D plugin to control Horiba spectrometer using Labspec6 AFM server protocol
* :feature:`0` Added new DAQ_Move plugin to control Newport ESP100 motion controllers
* :feature:`0` Added new DAQ_Viewer0D plugin for keithley 2110 using visa
* :feature:`0` Added new DAQ_Move plugin for smaract MCS controller
* :release:`1.2.2 <2019-09-30>`
* :feature:`0` Added shutter options for the Andor Camera
* :release:`1.2.1 <2019-09-29>`
* :feature:`0` Modified information string so that user know which plugin has not been loaded. Specific requirements concerning plugins have been removed, users have to install them is they need a specific plugin
* :release:`1.2.0 <2019-05-13>`
* :release:`1.1.1 <2019-05-13>`
* :bug:`0` Fixed package dependencies for the The Imaging source plugin
* :release:`1.1.0 <2019-05-07>`
* :feature:`0` DAQ_2DViewer plugins: new plugins for The imaging source camera's and GeniCAm compliant cameras
* :feature:`0` DAQ_Move_plugins: added the method *set_position_relative_with_scaling* to have correct steps in
  relative motion
  when scaling options are set
* :release:`1.0.4 <2019-04-01>`
* :feature:`0` Added a plugin for Stanford research SR830 lockin amplifier
* :feature:`0` Added a plugin for FLIM (Fluorescence lifetime imaging microscopy) measurements using both the
  Timeharp260 hardware from PicoQuant and the piezoconcept hardware
* :feature:`0` Added a plugin for Timeharp260 hardware from PicoQuant
* :bug:`0` Fixed and tested piezoconcept move plugin
* :feature:`0` Added a plugin for old mercury controller from Physik Instrumente
* :bug:`0` Fixed dll matching for the PI move plugin
* :feature:`0` Added a plugin for old mercury controller from Physik Instrumente
* :release:`1.0.2 <2019-01-16>`
* :bug:`0` fixed exposure time set in Ocean Optics plugin
* :bug:`0` wrong call to orsay_STEM move plugin
* :release:`1.0.0 <2018-12-18>`
* :feature:`0` Renamed all modules with lowercase. Created the repository out of pymodaq for parallel development


