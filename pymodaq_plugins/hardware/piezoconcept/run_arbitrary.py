# -*- coding: utf-8 -*-
"""
Created on Thu Mar 14 14:54:55 2019

@author: flim-users
"""
import time
import numpy as np
from pymodaq_plugins.hardware.piezoconcept.piezoconcept import PiezoConcept, Position, Time
from pymodaq.daq_utils.daq_utils import set_scan_linear
#%%

stage = PiezoConcept()

stage.init_communication('COM6')
print(stage.get_controller_infos())
stage._write_command('CHAIO 1o2s')
stage._get_read()


#%%
stage.set_time_interval(Time(20,'m'))
stage.get_time_interval()
#%%
stage.get_position('X')
#%%
stage.get_position('Y')
#%%
offset = 100000

start_axis1 = -10000 +offset
start_axis2 = -10000 +offset
stop_axis1 = 10000 +offset
stop_axis2 = 10000 +offset
step_axis1 = 2000
step_axis2 = 2000

scan_params = set_scan_linear(start_axis1,start_axis2,stop_axis1,stop_axis2,step_axis1,step_axis2,back_and_force=True)
positions = scan_params.positions
#%%
stage.move_axis(pos = Position(pos = offset, unit = 'n'))
stage.move_axis(pos = Position(axis = 'Y', pos = offset, unit = 'n'))
stage.set_positions_arbitrary(positions)

#%%
for ind_run in range(1):
    stage.run_arbitrary()
    info= ''
    while 'Completed' not in info:
        time.sleep(0.1)
        info = stage._get_read()
        print(info)
    print(info)
#%%
stage.close_communication()
