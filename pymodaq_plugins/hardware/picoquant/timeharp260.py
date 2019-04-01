"""
Class controlling timeharp 260 hardware. Wrapper based on the C library th260LIB.dll
"""
import sys
from ctypes import windll, create_string_buffer, POINTER, byref, pointer
from ctypes import c_uint, c_int, c_char, c_char_p, c_void_p, c_short, c_long, c_bool, c_double, c_uint64, c_uint32, Array, CFUNCTYPE, WINFUNCTYPE
from ctypes import c_ushort, c_ulong, c_float
import os
from enum import IntEnum
import platform
from pymodaq.daq_utils.daq_utils import winfunc, cfunc
from typing import TypeVar, Iterable, Tuple, List
from bitstring import BitArray, Bits
import numpy as np

__author__ = "Sébastien Weber"
__status__ = "alpha"
__version__ = "0.1"

import sys
is_64bits = sys.maxsize > 2**32

class ErrorCodes(IntEnum):
    TH260_ERROR_NONE = 0
    TH260_ERROR_DEVICE_OPEN_FAIL = -1
    TH260_ERROR_DEVICE_BUSY = -2
    TH260_ERROR_DEVICE_HEVENT_FAIL = -3
    TH260_ERROR_DEVICE_CALLBSET_FAIL = -4
    TH260_ERROR_DEVICE_BARMAP_FAIL = -5
    TH260_ERROR_DEVICE_CLOSE_FAIL = -6
    TH260_ERROR_DEVICE_RESET_FAIL = -7
    TH260_ERROR_DEVICE_GETVERSION_FAIL = -8
    TH260_ERROR_DEVICE_VERSION_MISMATCH = -9
    TH260_ERROR_DEVICE_NOT_OPEN = -10
    TH260_ERROR_DEVICE_LOCKED = -11
    TH260_ERROR_DEVICE_DRIVERVER_MISMATCH = -12
    TH260_ERROR_INSTANCE_RUNNING = -16
    TH260_ERROR_INVALID_ARGUMENT = -17
    TH260_ERROR_INVALID_MODE = -18
    TH260_ERROR_INVALID_OPTION = -19
    TH260_ERROR_INVALID_MEMORY = -20
    TH260_ERROR_INVALID_RDATA = -21
    TH260_ERROR_NOT_INITIALIZED = -22
    TH260_ERROR_NOT_CALIBRATED = -23
    TH260_ERROR_DMA_FAIL = -24
    TH260_ERROR_XTDEVICE_FAIL = -25
    TH260_ERROR_FPGACONF_FAIL = -26
    TH260_ERROR_IFCONF_FAIL = -27
    TH260_ERROR_FIFORESET_FAIL = -28
    TH260_ERROR_THREADSTATE_FAIL = -29
    TH260_ERROR_THREADLOCK_FAIL = -30
    TH260_ERROR_USB_GETDRIVERVER_FAIL = -32
    TH260_ERROR_USB_DRIVERVER_MISMATCH = -33
    TH260_ERROR_USB_GETIFINFO_FAIL = -34
    TH260_ERROR_USB_HISPEED_FAIL = -35
    TH260_ERROR_USB_VCMD_FAIL = -36
    TH260_ERROR_USB_BULKRD_FAIL = -37
    TH260_ERROR_LANEUP_TIMEOUT = -40
    TH260_ERROR_DONEALL_TIMEOUT = -41
    TH260_ERROR_MB_ACK_TIMEOUT = -42
    TH260_ERROR_MACTIVE_TIMEOUT = -43
    TH260_ERROR_MEMCLEAR_FAIL = -44
    TH260_ERROR_MEMTEST_FAIL = -45
    TH260_ERROR_CALIB_FAIL = -46
    TH260_ERROR_REFSEL_FAIL = -47
    TH260_ERROR_STATUS_FAIL = -48
    TH260_ERROR_MODNUM_FAIL = -49
    TH260_ERROR_DIGMUX_FAIL = -50
    TH260_ERROR_MODMUX_FAIL = -51
    TH260_ERROR_MODFWPCB_MISMATCH = -52
    TH260_ERROR_MODFWVER_MISMATCH = -53
    TH260_ERROR_MODPROPERTY_MISMATCH = -54
    TH260_ERROR_INVALID_MAGIC = -55
    TH260_ERROR_INVALID_LENGTH = -56
    TH260_ERROR_EEPROM_F01 = -64
    TH260_ERROR_EEPROM_F02 = -65
    TH260_ERROR_EEPROM_F03 = -66
    TH260_ERROR_EEPROM_F04 = -67
    TH260_ERROR_EEPROM_F05 = -68
    TH260_ERROR_EEPROM_F06 = -69
    TH260_ERROR_EEPROM_F07 = -70
    TH260_ERROR_EEPROM_F08 = -71
    TH260_ERROR_EEPROM_F09 = -72
    TH260_ERROR_EEPROM_F10 = -73
    TH260_ERROR_EEPROM_F11 = -74
    TH260_ERROR_UNSUPPORTED_FUNCTION = -80

    @classmethod
    def names(self):
        names=self.__members__.items()
        return [name for name, member in self.__members__.items()]


def errorstring(value):
    try:
        return ErrorCodes(value).name
    except:
        raise IOError('{}: Unkown error code return'.format(value))


class Th260(object):
    """
    Wrapper object around the TH260LIB dll from Picoquant Timeharp 260
    """
    def __init__(self):
        super(Th260, self).__init__()

        libpath = os.path.dirname(__file__)
        if platform.system() == "Windows":
            if is_64bits:
                libname = os.path.join(libpath, "th260lib64.dll")
            else:
                libname = os.path.join(libpath, "th260lib.dll")
        else:
            raise OSError('Only supported on windows')

        self._dll = windll.LoadLibrary(libname)
        self.create_prototypes()
        self.histogram_length = 0 #to get/set with self.TH260_SetHistoLen
        self.Nchannels = 0 #is set within self.TH260_GetNumOfInputChannels


    def TH260_GetErrorString(self, code: int):
        """"

        Parameters
        ----------
        code: (int) error code as returned from the TH260 library functions

        Returns
        -------
        str: translated error code
        """
        buffer = create_string_buffer(40)
        bp = c_char_p(buffer.value)
        res = self._TH260_GetErrorString(bp, code)
        if res == 0:
            return bp.value.decode()
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_GetLibraryVersion(self):
        bp = c_char_p(create_string_buffer(8).value)
        res = self._TH260_GetLibraryVersion(bp)
        if res == 0:
            return bp.value.decode()
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_OpenDevice(self, device: int = 0):
        """

        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)

        Returns
        -------
        str: serial number of the hardware
        """
        serialp = c_char_p(create_string_buffer(8).value)
        res = self._TH260_OpenDevice(device, serialp)
        if res == 0:
            return serialp.value.decode()
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_CloseDevice(self, device: int = 0):
        """

        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        """

        res = self._TH260_CloseDevice(device)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_Initialize(self, device: int = 0, mode: int = 0):
        """
        Init the Device
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        mode: (int) measurement mode
                        0 = histogramming mode
                        2 = T2 mode
                        3 = T3 mode
        """
        res = self._TH260_Initialize(device, mode)
        if res == 0:
            self.Nchannels = self.TH260_GetNumOfInputChannels(device)
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_GetHardwareInfo(self, device: int = 0):
        """

        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)

        Returns
        -------
        tuple of str listing the hardware model, part number and version
        """
        # modelp = c_char_p(create_string_buffer(16).value)
        # partp = c_char_p(create_string_buffer(8).value)
        # versionp = c_char_p(create_string_buffer(16).value)
        # res = self._TH260_GetHardwareInfo(device, modelp, partp, versionp)
        modelp = create_string_buffer(16)
        partp = create_string_buffer(8)
        versionp = create_string_buffer(16)
        res = self._dll.TH260_GetHardwareInfo(device, byref(modelp), byref(partp), byref(versionp))

        if res == 0:
            return modelp.value.decode(), partp.value.decode(), versionp.value.decode()
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_GetSerialNumber(self, device: int = 0):
        """

        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)

        Returns
        -------
        str: serial number
        """
        serialp = c_char_p(create_string_buffer(8).value)
        res = self._TH260_GetSerialNumber(device, serialp)
        if res == 0:
            return serialp.value.decode()
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_GetFeatures(self, device: int = 0):
        """
        Use the predefined bit feature values in th260defin.h (FEATURE_xxx) to extract individual bits through a bitwise AND.
        Typically this is only for information, or to check if your board has a specific (optional) capability.
        #define FEATURE_DLL       0x0001  // DLL License available
        #define FEATURE_TTTR      0x0002  // TTTR mode available
        #define FEATURE_MARKERS   0x0004  // Markers available
        #define FEATURE_LOWRES    0x0008  // Long range mode available
        #define FEATURE_TRIGOUT   0x0010  // Trigger output available
        #define FEATURE_PROG_TD   0x0020  // Programmable deadtime available
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)

        Returns
        -------
        list of str listing the hardware features
        """
        feature = c_int()
        res = self._TH260_GetFeatures(device, byref(feature))
        ret=[]

        if res == 0:
            feature = Bits(int=feature.value, length=32)
            if len(feature.find('0x0001')) != 0:
                ret.append("FEATURE_DLL")
            if len(feature.find('0x0002')) != 0:
                ret.append("FEATURE_TTTR")
            if len(feature.find('0x0004')) != 0:
                ret.append("FEATURE_MARKERS")
            if len(feature.find('0x0008')) != 0:
                ret.append("FEATURE_LOWRES")
            if len(feature.find('0x0010')) != 0:
                ret.append("FEATURE_TRIGOUT")
            if len(feature.find('0x0020')) != 0:
                ret.append("FEATURE_PROG_TD")

            return ret
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_GetBaseResolution(self, device: int = 0):
        """
        The value returned in binsteps is the maximum value allowed for the TH260_SetBinning function.
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)

        Returns
        -------
        double: resolution in ps
        int: maximal allowed bin steps
        """
        resolution = c_double()
        binsteps = c_int()
        res = self._TH260_GetBaseResolution(device, byref(resolution), byref(binsteps))
        if res == 0:
            return resolution.value, binsteps.value
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_GetNumOfInputChannels(self, device: int = 0):
        """
        The number of input channels is counting only the regular detector channels. It does not count the sync channel. Nevertheless,
        it is possible to connect a detector also to the sync channel, e.g. in histogramming mode for antibunching or in T2
        mode.
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)

        Returns
        -------
        int: number of channels
        """
        Nchan = c_int()
        res = self._TH260_GetNumOfInputChannels(device, byref(Nchan))
        if res == 0:
            return Nchan.value
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetTimingMode(self, device: int = 0, mode: int= 0):
        """
        TimeHarp 260 P only
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        mode: (int) 0 = Hires (25ps)
                    1 = Lowres (2.5 ns, a.k.a. “Long range”) will change the base resolution of the board
        """

        res = self._TH260_SetTimingMode(device, mode)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetSyncDiv(self, device: int = 0, div: int= 1):
        """
        The number of input channels is counting only the regular detector channels. It does not count the sync channel. Nevertheless,
        it is possible to connect a detector also to the sync channel, e.g. in histogramming mode for antibunching or in T2
        mode.
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        div: (int) sync rate divider (1, 2, 4, .., SYNCDIVMAX) #define SYNCDIVMAX		8
        """
        res = self._TH260_SetSyncDiv(device, div)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetSyncCFD(self, device: int = 0, level: int= -100, zerox: int= -10):
        """
        set crossingss specs for sync
        // TimeHarp 260 P only
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        level: (int) CFD discriminator level in millivolts minimum = CFDLVLMIN (-1200) maximum = CFDLVLMAX (0)
        zerox: (int) CFD zero cross level in millivolts minimum = CFDZCMIN (-40) maximum = CFDZCMIN (0)
        """
        res = self._TH260_SetSyncCFD(device, level, zerox)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetSyncEdgeTrg(self, device: int = 0, level: int= -100, edge: int= 0):
        """
        // TimeHarp 260 N only
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        level: (int) Trigger level in millivolts minimum = CFDLVLMIN (-1200) maximum = CFDLVLMAX (0)
        edge: (int) Trigger edge 0 = falling, 1 = rising
        """
        res = self._TH260_SetSyncEdgeTrg(device, level, edge)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetSyncChannelOffset(self, device: int = 0, value: int= 0):
        """
        Trigger temporal offset in ps
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        value: (int) sync timing offset in ps minimum = CHANOFFSMIN (-99999) maximum = CHANOFFSMAX (99999)
        """
        res = self._TH260_SetSyncChannelOffset(device, value)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetInputCFD(self, device: int = 0, channel: int= 0, level: int= -100, zerox: int= -10):
        """
        // TimeHarp 260 P only
        set crossingss specs for channels
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        channel: (int) input channel index 0..1
        level: (int) CFD discriminator level in millivolts minimum = CFDLVLMIN (-1200) maximum = CFDLVLMAX (0)
        zerox: (int) CFD zero cross level in millivolts minimum = CFDZCMIN (-40) maximum = CFDZCMIN (0)
        """
        res = self._TH260_SetInputCFD(device, channel, level, zerox)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetInputEdgeTrg(self, device: int = 0, channel: int= 0, level: int= -100, edge: int= 0):
        """
        // TimeHarp 260 N only
        set edges specs for channels
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        channel: (int) input channel index 0..1
        level: (int) Trigger level in millivolts minimum = CFDLVLMIN (-1200) maximum = CFDLVLMAX (0)
        edge: (int) Trigger edge 0 = falling, 1 = rising"""
        res = self._TH260_SetInputCFD(device, channel, level, edge)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetInputChannelOffset(self, device: int = 0, channel: int= 0, value: int= 0):
        """
        Channel temporal offset in ps
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        channel: (int) input channel index 0..1
        value: (int) sync timing offset in ps minimum = CHANOFFSMIN (-99999) maximum = CHANOFFSMAX (99999)
        """
        res = self._TH260_SetInputChannelOffset(device, channel, value)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetInputChannelEnable(self, device: int = 0, channel: int= 0, enable: bool= True):
        """
        enable/disable selected channel
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        channel: (int) input channel index 0..1
        enable: (bool) desired enable state of the input channel False = disabled, True = enabled
        """
        res = self._TH260_SetInputChannelEnable(device, channel, c_int(enable))
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetInputDeadTime(self, device: int = 0, channel: int= 0, tdcode: int= 0):
        """
        Trigger temporal offset in ps
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        channel: (int) input channel index 0..1
        tdcode: (int) code for desired deadtime of the input channel minimum = TDCODEMIN, maximum = TDCODEMAX

        notes
        -----
        The codes 0..7 correspond to approximate deadtimes of 24, 44, 66, 88 112, 135, 160 and 180 ns. Exact values are subject
        to production tolerances on the order of 10%. This feature is not available in boards produced before April 2015 but can be
        upgraded on request. The main purpose is that of suppressing artefacts (afterpulsing) produced by some types of detectors.
        Whether or not a given board supports this feature can be checked via TH260_GetFeatures and the bit mask FEATURE_
        PROG_TD as defined in thdefin.h. Note that the programmable deadtime is not available for the sync input.
        """
        res = self._TH260_SetInputDeadTime(device, channel, tdcode)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetStopOverflow(self, device: int = 0, stop_ovfl: bool= True, stopcount: int=4294967295):
        """
        This setting determines if a measurement run will stop if any channel reaches the maximum set by stopcount. If stop_ofl
        is 0 the measurement will continue but counts above STOPCNTMAX in any bin will be clipped.
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        stop_ovfl: (bool) False = do not stop, True = do stop on overflow
        stopcount: (int>=0)
        """

        res = self._TH260_SetStopOverflow(device, c_int(stop_ovfl), stopcount)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetBinning(self, device: int = 0, binning: int= 0):
        """
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        binning: (int) measurement binning code
                    minimum = 0 (smallest, i.e. base resolution)
                    maximum = (MAXBINSTEPS-1) (largest) #define MAXBINSTEPS	22// get actual number via TH260_GetBaseResolution() !
        """
        res = self._TH260_SetBinning(device, binning)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetHistoLen(self, device: int = 0, lencode: int= 0):
        """
        This sets the number of time bins in histogramming and T3 mode. It is not meaningful in T2 mode.
        returns the current length (time bin count) of histograms
        calculated according to: actuallen = 1024*(2^lencode)
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        lencode: (int) histogram length code
                    minimum = 0
                    maximum = MAXLENCODE (default)
        Returns
        -------
        int: current length
        """
        actuallen = c_int()
        res = self._TH260_SetHistoLen(device, lencode, byref(actuallen))
        if res == 0:
            self.histogram_length = actuallen.value
            return actuallen.value
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_ClearHistMem(self, device: int = 0):
        """
        This clears the histogram memory. It is not meaningful in T2 and T3 mode.
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        """
        res = self._TH260_ClearHistMem(device)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetMeasControl(self, device: int = 0, meascontrol: int= 0, startedge: int= 0, stopedge: int= 0):
        """
        This is a very specialized routine for externally (hardware) controlled measurements. Normally it is not needed.
        See section 5.5 for details.
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        meascontrol: (int) measurement control code
                        0 = MEASCTRL_SINGLESHOT_CTC
                        1 = MEASCTRL_C1_GATED
                        2 = MEASCTRL_C1_START_CTC_STOP
        startedge: (int) edge selection code
                        0 = falling
                        1 = rising
        stopedge: (int) edge selection code
                        0 = falling
                        1 = rising
        """
        res = self._TH260_SetMeasControl(device, meascontrol, startedge, stopedge)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_StartMeas(self, device: int = 0, tacq: int= 1000):
        """
        This starts a measurement in the current measurement mode. Should be called after all settings are done.
        Previous measurements should be stopped before calling this routine again.
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        tacq: acquisition time in milliseconds
            minimum = ACQTMIN (1) // ms, for TH260_StartMeas
            maximum = ACQTMAX (360000000)// ms  (100*60*60*1000ms = 100h)
        """
        res = self._TH260_StartMeas(device, tacq)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_StopMeas(self, device: int = 0):
        """
        This must be called after the acquisition time is expired. Can also be used to force stop before the acquisition time expires.
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        """
        res = self._TH260_StopMeas(device)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_CTCStatus(self, device: int = 0):
        """
        Acquisition status
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        Returns
        -------
        bool: current status (True: running, False: acquisition has ended)
        """
        ctcstatus = c_int()
        res = self._TH260_CTCStatus(device, byref(ctcstatus))
        if res == 0:
            return bool(ctcstatus.value)
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_GetHistogram(self, device: int = 0, data_pointer: POINTER(c_uint32) = pointer(c_uint32(0)),  channel: int= 0, clear: bool= False):
        """
        Get histogram data
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        channel: (int) input channel index 0..nchannels-1
        clear: (bool) denotes the action upon completing the reading process
                False = keeps the histogram in the acquisition buffer
                True = clears the acquisition buffer

        Returns
        -------
        ndarray: content of the histogram

        Notes
        -----
        The histogram buffer size actuallen must correspond to the value obtained through TH260_SetHistoLen().
        The maximum input channel index must correspond to nchannels-1 as obtained through TH260_GetNumOfInputChannels().
        """
        res = self._dll.TH260_GetHistogram(device, data_pointer, channel, c_int(clear))
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_GetResolution(self, device: int = 0):
        """
        Get resolution at the current binning (histogram bin width) in ps
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)

        Returns
        -------
        float64: resolution at the current binning (histogram bin width) in ps

        Notes
        -----
        This is meaningful only in histogramming and T3 mode. T2 mode always runs at the boards's base resolution.
        """
        resolution = c_double()
        res = self._TH260_GetResolution(device, byref(resolution))
        if res == 0:
            return resolution.value
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_GetSyncRate(self, device: int = 0):
        """
        This is used to get the pulse rate at the sync input. The result is internally corrected for the current sync divider setting.
        Allow at least 100 ms after TH260_Initialize or TH260_SetSyncDivider to get a stable rate reading. Similarly,
        wait at least 100 ms to get a new reading. This is the gate time of the hardware counters.
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)

        Returns
        -------
        int: current sync rate
         """
        syncrate = c_int()
        res = self._TH260_GetSyncRate(device, byref(syncrate))
        if res == 0:
            return syncrate.value
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_GetCountRate(self, device: int = 0, channel: int= 0):
        """
        current count rate of this input channel
        Allow at least 100 ms after TH260_Initialize to get a stable rate reading. Similarly, wait at least 100 ms to get a new reading.
        This is the gate time of the hardware counters. The maximum channel index must correspond to nchannels-1 as obtained
        through TH260_GetNumOfInputChannels().
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        channel: (int) number of the input channel 0..nchannels-1
        Returns
        -------
        int: current count rate of this input channel
         """
        cntrate = c_int()
        res = self._TH260_GetCountRate(device, channel, byref(cntrate))
        if res == 0:
            return cntrate.value
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_GetFlags(self, device: int = 0):
        """
        #define FLAG_OVERFLOW     0x0001  // histo mode only
        #define FLAG_FIFOFULL     0x0002
        #define FLAG_SYNC_LOST    0x0004  // T3 mode only
        #define FLAG_EVTS_DROPPED 0x0008  // dropped events due to high input rate
        #define FLAG_SYSERROR     0x0010  // hardware error, must contact support
        #define FLAG_SOFTERROR    0x0020  // software error, must contact support
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        Returns
        -------
        list of strings: current list of flags
         """
        flags = c_int()
        res = self._TH260_GetFlags(device, byref(flags))
        if res == 0:
            ret=[]
            #flags = Bits(int=flags.value, length=32)
            if flags.value & 0x0001 > 1:
                ret.append('OVERFLOW')
            if flags.value & 0x0002 > 1:
                ret.append('FIFOFULL')
            if flags.value & 0x0004 > 1:
                ret.append('SYNC_LOST')
            if flags.value & 0x0008 > 1:
                ret.append('EVTS_DROPPED')
            if flags.value & 0x0010 > 1:
                ret.append('SYSERROR')
            if flags.value & 0x0020 > 1:
                ret.append('SOFTERROR')
            return ret
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_GetElapsedMeasTime(self, device: int = 0):
        """
        During a measurememt this can be called to obtain the measurement time that has elapsed so far. After a measurement it
        will return the time that actually elapsed before the measurement was stopped (e.g. due to histogram overflow or forced
        stop).
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        Returns
        -------
        float: the elapsed measurement time in ms
         """
        elapsed = c_double()
        res = self._TH260_GetElapsedMeasTime(device, byref(elapsed))
        if res == 0:
            return elapsed.value
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_GetWarnings(self, device: int = 0):
        """
        #define WARNING_SYNC_RATE_ZERO				0x0001
        #define WARNING_SYNC_RATE_VERY_LOW			0x0002
        #define WARNING_SYNC_RATE_TOO_HIGH			0x0004
        #define WARNING_INPT_RATE_ZERO				0x0010
        #define WARNING_INPT_RATE_TOO_HIGH			0x0040
        #define WARNING_INPT_RATE_RATIO				0x0100
        #define WARNING_DIVIDER_GREATER_ONE			0x0200
        #define WARNING_TIME_SPAN_TOO_SMALL			0x0400
        #define WARNING_OFFSET_UNNECESSARY			0x0800
        #define WARNING_DIVIDER_TOO_SMALL			0x1000
        #define WARNING_COUNTS_DROPPED				0x2000
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        Returns
        -------
        str: concatenation of current warnings
         """
        self.TH260_GetSyncRate(device)
        for ind in range(self.Nchannels):
            self.TH260_GetCountRate(device, ind)
        warnings = c_int()
        res = self._TH260_GetWarnings(device, byref(warnings))
        if res == 0:
            text = self.TH260_GetWarningsText(device, warnings.value)
            return text
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_GetWarningsText(self, device: int = 0, warnings: int= 0):
        """
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        warnings: (int) integer bitfield obtained from TH260_GetWarnings
        Returns
        -------
        str: all warnings as text
         """
        text = create_string_buffer(16384)

        res = self._dll.TH260_GetWarningsText(device, byref(text), warnings)
        if res == 0:
            return text.value.decode()
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_GetHardwareDebugInfo(self, device: int = 0):
        """
        Call this routine if you receive the error code TH260_ERROR_STATUS_FAIL or the flag FLAG_SYSERROR.
        See th260defin.h and errorcodes.h for the numerical values of these codes. Provide the result for support.
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        Returns
        -------
        str: all warnings as text
         """
        text = c_char_p(create_string_buffer(16384).value)
        res = self._TH260_GetHardwareDebugInfo(device, text)
        if res == 0:
            return text.value.decode()
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_GetSyncPeriod(self, device: int = 0):
        """
        Call this routine if you receive the error code TH260_ERROR_STATUS_FAIL or the flag FLAG_SYSERROR.
        See th260defin.h and errorcodes.h for the numerical values of these codes. Provide the result for support.
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        Returns
        -------
        float: returns the sync period in seconds
         """
        period = c_double()
        res = self._TH260_GetSyncPeriod(device, period)
        if res == 0:
            return period.value
        else:
            raise IOError(ErrorCodes(res).name)


    def TH260_ReadFiFo(self, device: int = 0, count: int= 0, buffer_ptr=POINTER(c_uint)()):
        """
        Read queue in TTTR mode
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        count: (int) number of TTTR records the buffer can hold (min = TTREADMIN (128), max = TTREADMAX (131072))
        buffer_ptr (POINTER(c_uint)()): pointer to a 4096 aligned buffer
        Returns
        -------
        int: the number of TTTR records received
        Notes
        -----
        CPU time during wait for completion will be yielded to other processes / threads. The call will return after a timeout
        period of a few ms if no more data could be fetched. The buffer must not be accessed until the call returns.
        New in v 3.1: Note that the buffer must be aligned on a 4096-byte boundary in order to allow efficient DMA transfers.
        If the buffer does not meet this requirement the library will use an internal buffer and copy the data. This slows down data
        throughput.
         """
        nactual = c_int()
        res = self._TH260_ReadFiFo(device, buffer_ptr, count, byref(nactual))
        if res == 0:
            return nactual.value
        else:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetMarkerEdges(self, device: int = 0, me0: int= 0, me1: int= 0, me2: int= 0, me3: int= 0):
        """

        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        en<n>: (int) active edge of marker signal <n>,
                    0 = falling,
                    1 = rising
         """
        res = self._TH260_SetMarkerEdges(device, me0, me1, me2, me3)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetMarkerEnable(self, device: int = 0, en0: int= 0, en1: int= 0, en2: int= 0, en3: int= 0):
        """

        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        en<n>: (int) desired enable state of marker signal <n>,
                0 = disabled,
                1 = enabled
         """
        res = self._TH260_SetMarkerEnable(device, en0, en1, en2, en3)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def TH260_SetMarkerHoldoffTime(self, device: int = 0, holdofftime: int= 0):
        """
        Parameters
        ----------
        device: (int) device index if multiple devices 0..3 (default 0)
        holdofftime: (int) desired holdoff time for marker signals in nanoseconds
                        min = 0,
                        max = 25500
        Notes
        -----
        Note: After receiving a marker the system will suppress subsequent markers for the duration of holdofftime (ns). This can be
        used to suppress glitches on the marker signals. This is only a workaround for poor signals. Try to solve the problem at its
        origin, i.e. the quality of marker source and cabling.
        """
        res = self._TH260_SetMarkerHoldoffTime(device, holdofftime)
        if res != 0:
            raise IOError(ErrorCodes(res).name)

    def create_prototypes(self):
        """
        Declaring functions from the dll with appropriate arguments to ovoid crashing
        """
        # extern int _stdcall TH260_GetLibraryVersion(char* version);
        self._TH260_GetLibraryVersion = winfunc('TH260_GetLibraryVersion', self._dll, c_int, ('vers', c_char_p, 1))

        # extern int _stdcall TH260_GetErrorString(char* errstring, int errcode);
        self._TH260_GetErrorString = winfunc('TH260_GetErrorString', self._dll, c_int, ('errstring', c_char_p, 1),
                                             ('errcode', c_int, 1))

        # extern int _stdcall TH260_OpenDevice(int devidx, char* serial);
        self._TH260_OpenDevice = winfunc('TH260_OpenDevice', self._dll, c_int, ('devidx', c_int, 1, 0),
                                         ('serial', c_char_p, 1))

        # extern int _stdcall TH260_CloseDevice(int devidx);
        self._TH260_CloseDevice = winfunc('TH260_CloseDevice', self._dll, c_int, ('devidx', c_int, 1, 0))

        # extern int _stdcall TH260_Initialize(int devidx, int mode);
        self._TH260_Initialize = winfunc('TH260_Initialize', self._dll, c_int, ('devidx', c_int, 1, 0),
                                         ('mode', c_int, 1, 0))

        # //all functions below can only be used after TH260_Initialize
        # extern int _stdcall TH260_GetHardwareInfo(int devidx, char* model, char* partno, char* version);
        self._TH260_GetHardwareInfo = winfunc('TH260_GetHardwareInfo', self._dll, c_int, ('devidx', c_int, 1, 0),
                                              ('model', c_char_p, 1), ('partno', c_char_p, 1),
                                              ('version', c_char_p, 1))

        # extern int _stdcall TH260_GetSerialNumber(int devidx, char* serial);
        self._TH260_GetSerialNumber = winfunc('TH260_GetSerialNumber', self._dll, c_int, ('devidx', c_int, 1, 0),
                                              ('serial', c_char_p, 1))

        # extern int _stdcall TH260_GetFeatures(int devidx, int* features);
        self._TH260_GetFeatures = winfunc('TH260_GetFeatures', self._dll, c_int, ('devidx', c_int, 1, 0),
                                                ('features', POINTER(c_int), 1))

        # extern int _stdcall TH260_GetBaseResolution(int devidx, double* resolution, int* binsteps);
        self._TH260_GetBaseResolution = winfunc('TH260_GetBaseResolution', self._dll, c_int,
                                                      ('devidx', c_int, 1, 0),
                                                ('resolution', POINTER(c_double), 1),
                                                ('binsteps', POINTER(c_int), 1))


        # extern int _stdcall TH260_GetNumOfInputChannels(int devidx, int* nchannels);
        self._TH260_GetNumOfInputChannels = winfunc('TH260_GetNumOfInputChannels', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('nchannels', POINTER(c_int), 1, 0))

        #
        # extern int _stdcall TH260_SetSyncDiv(int devidx, int div);
        self._TH260_SetSyncDiv = winfunc('TH260_SetSyncDiv', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('div', c_int, 1))

        # extern int _stdcall TH260_SetSyncCFD(int devidx, int level, int zc);         //TH 260 Pico only
        self._TH260_SetSyncCFD = winfunc('TH260_SetSyncCFD', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('level', c_int, 1),
                                                    ('zc', c_int, 1))

        # extern int _stdcall TH260_SetSyncEdgeTrg(int devidx, int level, int edge);   //TH 260 Nano only
        self._TH260_SetSyncEdgeTrg = winfunc('TH260_SetSyncEdgeTrg', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('level', c_int, 1),
                                                    ('edge', c_int, 1))

        # extern int _stdcall TH260_SetSyncChannelOffset(int devidx, int value);
        self._TH260_SetSyncChannelOffset = winfunc('TH260_SetSyncChannelOffset', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('value', c_int, 1))

        #
        # extern int _stdcall TH260_SetInputCFD(int devidx, int channel, int level, int zc);       //TH 260 Pico only
        self._TH260_SetInputCFD = winfunc('TH260_SetInputCFD', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('channel', c_int, 1),
                                                    ('level', c_int, 1),
                                                    ('zc', c_int, 1))

        # extern int _stdcall TH260_SetInputEdgeTrg(int devidx, int channel, int level, int edge); //TH 260 Nano only
        self._TH260_SetInputEdgeTrg = winfunc('TH260_SetInputEdgeTrg', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('channel', c_int, 1),
                                                    ('level', c_int, 1),
                                                    ('edge', c_int, 1))

        # extern int _stdcall TH260_SetInputChannelOffset(int devidx, int channel, int value);
        self._TH260_SetInputChannelOffset = winfunc('TH260_SetInputChannelOffset', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('channel', c_int, 1),
                                                    ('value', c_int, 1))

        # extern int _stdcall TH260_SetInputChannelEnable(int devidx, int channel, int enable);
        self._TH260_SetInputChannelEnable = winfunc('TH260_SetInputChannelEnable', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('channel', c_int, 1),
                                                    ('enable', c_int, 1))

        # extern int _stdcall TH260_SetInputDeadTime(int devidx, int channel, int tdcode); //needs TH 260 Pico >= April 2015
        self._TH260_SetInputDeadTime = winfunc('TH260_SetInputDeadTime', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('channel', c_int, 1),
                                                    ('tdcode', c_int, 1))
        #
        # extern int _stdcall TH260_SetTimingMode(int devidx, int mode); //TH 260 Pico only
        self._TH260_SetTimingMode = winfunc('TH260_SetTimingMode', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('mode', c_int, 1))

        # extern int _stdcall TH260_SetStopOverflow(int devidx, int stop_ovfl, unsigned int stopcount);
        self._TH260_SetStopOverflow = winfunc('TH260_SetStopOverflow', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('stop_ovfl', c_int, 1),
                                                    ('stopcount', c_uint, 1))

        # extern int _stdcall TH260_SetBinning(int devidx, int binning);
        self._TH260_SetBinning = winfunc('TH260_SetBinning', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('binning', c_int, 1))
        
        # extern int _stdcall TH260_SetOffset(int devidx, int offset);
        self._TH260_SetOffset = winfunc('TH260_SetOffset', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('offset', c_int, 1))
        
        # extern int _stdcall TH260_SetHistoLen(int devidx, int lencode, int* actuallen);
        self._TH260_SetHistoLen = winfunc('TH260_SetHistoLen', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('lencode', c_int, 1),
                                                    ('actuallen', POINTER(c_int), 1))

        # extern int _stdcall TH260_SetMeasControl(int devidx, int control, int startedge, int stopedge);
        self._TH260_SetMeasControl = winfunc('TH260_SetMeasControl', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('control', c_int, 1),
                                                    ('startedge', c_int, 1),
                                                    ('stopedge', c_int, 1))

        # extern int _stdcall TH260_SetTriggerOutput(int devidx, int period);
        self._TH260_SetTriggerOutput = winfunc('TH260_SetTriggerOutput', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('period', c_int, 1))
        #
        # extern int _stdcall TH260_ClearHistMem(int devidx);
        self._TH260_ClearHistMem = winfunc('TH260_ClearHistMem', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0))

        # extern int _stdcall TH260_StartMeas(int devidx, int tacq);
        self._TH260_StartMeas = winfunc('TH260_StartMeas', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('tacq', c_int, 1))

        # extern int _stdcall TH260_StopMeas(int devidx);
        self._TH260_StopMeas = winfunc('TH260_StopMeas', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0))

        # extern int _stdcall TH260_CTCStatus(int devidx, int* ctcstatus);
        self._TH260_CTCStatus = winfunc('TH260_CTCStatus', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('ctcstatus', POINTER(c_int), 1))
        #
        # extern int _stdcall TH260_GetHistogram(int devidx, unsigned int *chcount, int channel, int clear);
        self._TH260_GetHistogram = winfunc('TH260_GetHistogram', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('chcount', POINTER(c_uint), 1),
                                                    ('channel', c_int, 1),
                                                    ('clear', c_int, 1))

        # extern int _stdcall TH260_GetResolution(int devidx, double* resolution);
        self._TH260_GetResolution = winfunc('TH260_GetResolution', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('resolution', POINTER(c_double), 1))

        # extern int _stdcall TH260_GetSyncRate(int devidx, int* syncrate);
        self._TH260_GetSyncRate = winfunc('TH260_GetSyncRate', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('syncrate', POINTER(c_int), 1))

        # extern int _stdcall TH260_GetCountRate(int devidx, int channel, int* cntrate);
        self._TH260_GetCountRate = winfunc('TH260_GetCountRate', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('channel', c_int, 1),
                                                    ('cntrate', POINTER(c_int), 1))

        # extern int _stdcall TH260_GetFlags(int devidx, int* flags);
        self._TH260_GetFlags = winfunc('TH260_GetFlags', self._dll, c_int, ('devidx', c_int, 1, 0),
                                                    ('flags', POINTER(c_int), 1))

        # extern int _stdcall TH260_GetElapsedMeasTime(int devidx, double* elapsed);
        self._TH260_GetElapsedMeasTime = winfunc('TH260_GetElapsedMeasTime', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('elapsed', POINTER(c_double), 1))

        # extern int _stdcall TH260_GetSyncPeriod(int devidx, double* period);
        self._TH260_GetSyncPeriod = winfunc('TH260_GetSyncPeriod', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('period', POINTER(c_double), 1))
        #
        # extern int _stdcall TH260_GetWarnings(int devidx, int* warnings);
        self._TH260_GetWarnings = winfunc('TH260_GetWarnings', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('warnings', POINTER(c_int), 1))

        # extern int _stdcall TH260_GetWarningsText(int devidx, char* text, int warnings);
        self._TH260_GetWarningsText = winfunc('TH260_GetWarningsText', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('text', c_char_p, 1),
                                                    ('warnings', c_int, 1))

        # extern int _stdcall TH260_GetHardwareDebugInfo(int devidx, char *debuginfo);
        self._TH260_GetHardwareDebugInfo = winfunc('TH260_GetHardwareDebugInfo', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('debuginfo', c_char_p, 1))
        #
        # //for time tagging modes
        # extern int _stdcall TH260_SetMarkerEdges(int devidx, int me1, int me2, int me3, int me4);
        self._TH260_SetMarkerEdges = winfunc('TH260_SetMarkerEdges', self._dll, c_int,
                                                     ('devidx', c_int, 1, 0),
                                                     ('me1', c_int, 1, 0),
                                                     ('me2', c_int, 1, 0),
                                                     ('me3', c_int, 1, 0),
                                                     ('me4', c_int, 1, 0))

        # extern int _stdcall TH260_SetMarkerEnable(int devidx, int en1, int en2, int en3, int en4);
        self._TH260_SetMarkerEnable = winfunc('TH260_SetMarkerEnable', self._dll, c_int,
                                                  ('devidx', c_int, 1, 0),
                                                  ('en1', c_int, 1, 0),
                                                  ('en2', c_int, 1, 0),
                                                  ('en3', c_int, 1, 0),
                                                  ('en4', c_int, 1, 0))

        # extern int _stdcall TH260_SetMarkerHoldoffTime(int devidx, int holdofftime);
        self._TH260_SetMarkerHoldoffTime = winfunc('TH260_SetMarkerHoldoffTime', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('holdofftime', c_int, 1))

        # extern int _stdcall TH260_ReadFiFo(int devidx, unsigned int* buffer, int count, int* nactual);
        self._TH260_ReadFiFo = winfunc('TH260_ReadFiFo', self._dll, c_int,
                                                    ('devidx', c_int, 1, 0),
                                                    ('buffer', POINTER(c_uint), 1),
                                                    ('count', c_int, 1),
                                                    ('nactual', POINTER(c_int), 1))

if __name__ == '__main__':
    # obj = Th260()
    #
    # obj.TH260_OpenDevice()
    #
    # obj.TH260_Initialize()
    #
    # print(obj.TH260_GetHardwareInfo())
    #
    # print(obj.TH260_GetSerialNumber())
    #
    # print(obj.TH260_GetFeatures())
    #
    # print(obj.TH260_GetBaseResolution())
    #
    # print(obj.TH260_GetNumOfInputChannels())
    #
    # obj.TH260_CloseDevice()
    pass