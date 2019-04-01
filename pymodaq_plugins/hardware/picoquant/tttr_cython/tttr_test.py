import numpy as np
from phconvert import pqreader
import matplotlib.pyplot as plt

from pymodaq_plugins.hardware.picoquant.tttr_cython.tttr import extract_TTTR_histo_every_line, extract_TTTR_histo_every_pixels
import time
import tables

#%%
filebis = 'temp_data_091.h5'
h5file = tables.open_file(filebis)
ind_reading = 0
#%%
markers = h5file.get_node('/markers')[ind_reading:]
nanotimes = h5file.get_node('/nanotimes')[ind_reading:]

#%%
marker = 65
Nx = 11
Ny = 11
Ntime = 1024
marker = 65
#%%
t=time.perf_counter()
datas = extract_TTTR_histo_every_pixels(nanotimes,
                       markers,
                       marker=marker,
                       Nx=Nx,
                       Ny=Ny,
                       Ntime=Ntime,
                       ind_line_offset=0,
                       channel=0
                       
                       )
print(time.perf_counter()-t)
#%%
t=time.perf_counter()
bins = np.linspace(0, Ntime, Ntime + 1)

indexes_new_line = np.squeeze(np.argwhere(markers == marker))
if indexes_new_line.size == 0:
    indexes_new_line = [0, nanotimes.size]
    
datas = np.zeros((Nx, Ny, Ntime))
#%

for ind, index in enumerate(indexes_new_line[:-1]):
    data_line_tmp = nanotimes[indexes_new_line[ind] + 1:indexes_new_line[ind + 1]]
    time_splitted = np.linspace(np.min(data_line_tmp), np.max(data_line_tmp), Nx+1)[0:-1]
    
    #dispatch in given Nx bin
    ind_bins = np.digitize(data_line_tmp, time_splitted)
    
    
    splitted= -1*np.ones((Nx, np.max(np.bincount(ind_bins))))
    ind_splitted = np.zeros((Nx), dtype=np.int)
    
    #splitted = [[-10000] for ind in range(time_splitted.size)]
    for ind_ntime, ntime in enumerate(data_line_tmp):
        #splitted[ind_bins[ind_ntime] - 1].append(ntime)
        splitted[ind_bins[ind_ntime] - 1,ind_splitted[ind_bins[ind_ntime] - 1]]=ntime
        ind_splitted[ind_bins[ind_ntime]-1] += 1
                     
    for indx in range(Nx):
        datas[indx, int(ind % Ny)] += np.histogram(np.array(splitted[indx]), bins, range=None)[0]
print(time.perf_counter()-t)
#%%

fig = plt.figure(1)
fig.clear()
plt.plot(np.squeeze(datas.reshape((Nx*Ny,Ntime))).T)

#%% analysis with a marker for each pixel

t=time.perf_counter()
bins = np.linspace(0, Ntime, Ntime + 1)
markers_tot = markers[np.logical_or(markers==0,markers==65)]
nanotimes_tot = nanotimes[np.logical_or(markers==0,markers==65)]
indexes_new_line = np.squeeze(np.argwhere(markers == marker))

if indexes_new_line.size == 0:
    indexes_new_line = [0, nanotimes_tot.size]
    
datas = np.zeros((Nx, Ny, Ntime))
#%

for ind, index in enumerate(indexes_new_line[:-1]):

    data_line_tmp = nanotimes_tot[indexes_new_line[ind] + 1:indexes_new_line[ind + 1]]
    datas[ind%Nx,(ind//Nx)%Ny] += np.histogram(data_line_tmp, bins, range=None)[0]
    


print(time.perf_counter()-t)
#%%
if __name__ == '__main__':
    from PyQt5 import QtWidgets
    import sys
    from pymodaq.daq_utils.plotting.viewerND.viewerND_main import ViewerND
    
    app = QtWidgets.QApplication(sys.argv)
    form = QtWidgets.QWidget();
    prog = ViewerND()
    prog.show_data(datas, nav_axis=(0, 1))

    sys.exit(app.exec_())