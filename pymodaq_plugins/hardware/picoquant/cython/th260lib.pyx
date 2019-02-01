# th260lib64.pyx

cimport cth260lib


cdef class TH260:
    cdef int histogram_length, Nchannels, device

    def __cinit__(self, int dev = 0):
        self.histogram_length = 0 #to get/set with self.TH260_SetHistoLen
        self.Nchannels = 0 #is set within self.TH260_GetNumOfInputChannels
        self.device = dev

    cdef char* TH260_GetErrorString(self,int res):
        cdef char err_s[40]
        cdef char* error_string = err_s
        err=cth260lib.TH260_GetErrorString(error_string,res)
        py_string = <bytes> error_string
        return py_string.decode()


    def TH260_GetLibraryVersion(self):
        cdef char vers[8]
        cdef char* version = vers
        cdef int err = cth260lib.TH260_GetLibraryVersion(version)
        if err == 0:
            return version.decode()
        else:
            raise IOError(self.TH260_GetErrorString(err))


    def TH260_OpenDevice(self):
        cdef char ser[8]
        cdef char* serial = ser
        cdef int err = cth260lib.TH260_OpenDevice(self.device, serial)
        if err == 0:
            return serial.decode()
        else:
            raise IOError(self.TH260_GetErrorString(err))

