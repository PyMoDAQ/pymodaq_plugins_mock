# -*- coding: utf-8 -*-
import numpy as np
cimport numpy as np
 
def extract_TTTR_histo_every_line(np.ndarray[np.uint16_t, ndim=1] nanotimes,
                       np.ndarray[np.uint8_t, ndim=1] markers,
                       int marker=65,
                       int Nx=1,
                       int Ny=1,
                       int Ntime=512,
                       int ind_line_offset=0):
    """
    Extract histograms from photon tags and attributes them in the given pixel of the FLIM
    The marker is used to check where a new line within the image starts
    Parameters
    ----------
    nanotimes: (ndarray of uint16) photon arrival times (in timeharp units)
    markers: (ndarray of uint8) markers: 0 means the corresponding nanotime is a photon on detector 0,
                                         1 means the corresponding nanotime is a photon on detector 1,
                                         65 => Marker 1 event
                                         66 => Marker 2 event
                                         ...
                                         79 => Marker 15 event
                                         127 =>overflow
    marker: (int) the marker value corresponding to a new Y line within the image (for instance 65)
    Nx: (int) the number of pixels along the xaxis
    Ny: (int) the number of pixels along the yaxis
    Ntime: (int) the number of pixels alond the time axis
    ind_line_offset: (int) the offset of previously read lines

    Returns
    -------
    ndarray: FLIM hypertemporal image in the order (X, Y, time)
    """
    #%%
    cdef np.ndarray[np.int64_t, ndim=1] bins = np.linspace(0, Ntime, Ntime + 1, dtype=np.int64)
    cdef np.ndarray[np.float64_t, ndim=3] datas = np.zeros((Nx, Ny, Ntime))
    #%%
    cdef Py_ssize_t ind_line, ind_ntime, iline, indx
    
    cdef np.ndarray[np.uint16_t, ndim=1] data_line_tmp
    cdef np.ndarray[np.float64_t, ndim=1] time_splitted
    cdef np.ndarray[np.int16_t, ndim=2] splitted
    cdef np.ndarray[np.int32_t, ndim=1] ind_splitted
    cdef np.ndarray[np.uint64_t, ndim=1] indexes_new_line
    
    nanotimes = nanotimes[np.logical_or(markers == marker, markers == 0)]
    markers = markers[np.logical_or(markers == marker, markers == 0)]
    indexes_new_line = np.squeeze(np.argwhere(markers == marker)).astype(np.uint64)
    
    if indexes_new_line.size == 0:
        indexes_new_line = np.array([0, nanotimes.size], dtype=np.uint64)
    #print(indexes_new_line)
    for ind_line in range(indexes_new_line.size-1):
        #print(ind_line)
        data_line_tmp = nanotimes[indexes_new_line[ind_line] + 1:indexes_new_line[ind_line + 1]]
        time_splitted = np.linspace(np.min(data_line_tmp), np.max(data_line_tmp), Nx+1)[0:-1]
        #print(time_splitted)
        #dispatch in given Nx bin
        ind_bins = np.digitize(data_line_tmp, time_splitted)
        #print(ind_bins)
        splitted= np.int16(-1)*np.ones((Nx, np.max(np.bincount(ind_bins))), dtype=np.int16)
        ind_splitted = np.zeros((Nx), dtype=np.int32)
        
        #splitted = [[-10000] for ind_line in range(time_splitted.size)]
        for ind_ntime in range(data_line_tmp.size):
            #splitted[ind_bins[ind_ntime] - 1].append(ntime)
            splitted[ind_bins[ind_ntime] - 1,ind_splitted[ind_bins[ind_ntime] - 1]]=data_line_tmp[ind_ntime]
            ind_splitted[ind_bins[ind_ntime]-1] += 1
        #print(splitted)
        for indx in range(Nx):
            iline = np.int(ind_line%Ny)+ind_line_offset
            datas[indx, iline] += np.histogram(np.array(splitted[indx]), bins, range=None)[0]
            
    return datas

def extract_TTTR_histo_every_pixels(np.ndarray[np.uint16_t, ndim=1] nanotimes,
                       np.ndarray[np.uint8_t, ndim=1] markers,
                       int marker=65,
                       int Nx=1,
                       int Ny=1,
                       int Ntime=512,
                       int ind_line_offset=0,
                       int channel=0):
    """
    Extract histograms from photon tags and attributes them in the given pixel of the FLIM
    The marker is used to check where a new line within the image starts
    Parameters
    ----------
    nanotimes: (ndarray of uint16) photon arrival times (in timeharp units)
    markers: (ndarray of uint8) markers: 0 means the corresponding nanotime is a photon on detector 0,
                                         1 means the corresponding nanotime is a photon on detector 1,
                                         65 => Marker 1 event
                                         66 => Marker 2 event
                                         ...
                                         79 => Marker 15 event
                                         127 =>overflow
    marker: (int) the marker value corresponding to a new Y line within the image (for instance 65)
    Nx: (int) the number of pixels along the xaxis
    Ny: (int) the number of pixels along the yaxis
    Ntime: (int) the number of pixels alond the time axis
    ind_line_offset: (int) the offset of previously read lines
    channel: (int) marker of the specific channel (0 or 1) for channel 1 or 2

    Returns
    -------
    ndarray: FLIM hypertemporal image in the order (X, Y, time)
    """
    #%%
    cdef np.ndarray[np.int64_t, ndim=1] bins = np.linspace(0, Ntime, Ntime + 1, dtype=np.int64)
    cdef np.ndarray[np.float64_t, ndim=3] datas = np.zeros((Nx, Ny, Ntime))
    #%%
    cdef Py_ssize_t ind_line, ind_ntime, ix, iy, indx
    
    cdef np.ndarray[np.uint16_t, ndim=1] data_line_tmp
    cdef np.ndarray[np.uint64_t, ndim=1] indexes_new_line
    
    nanotimes = nanotimes[np.logical_or(markers == marker, markers == channel)]
    markers = markers[np.logical_or(markers == marker, markers == channel)]
    indexes_new_line = np.squeeze(np.argwhere(markers == marker)).astype(np.uint64)
    
    if indexes_new_line.size == 0:
        indexes_new_line = np.array([0, nanotimes.size], dtype=np.uint64)
    #print(indexes_new_line)
    for ind_line in range(indexes_new_line.size-1):
        #print(ind_line)
        data_line_tmp = nanotimes[indexes_new_line[ind_line] + 1:indexes_new_line[ind_line + 1]]
        ix = np.int((ind_line+ind_line_offset)%Nx)
        iy =np.int(((ind_line+ind_line_offset)//Nx)%Ny)
        datas[ix, iy, :] += np.histogram(data_line_tmp, bins, range=None)[0]
            
    return datas