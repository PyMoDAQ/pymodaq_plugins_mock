# Demo for access to TimeHarp 260 Hardware via TH260LIB.DLL v 3.1.
# The program performs a measurement based on hard coded settings.
# The resulting data is stored in a binary output file.
#
# Keno Goertz, PicoQuant GmbH, February 2018

import time
import ctypes as ct
from ctypes import byref
import sys
import struct

# From th260defin.h
LIB_VERSION = "3.1"
MAXDEVNUM = 4
MODE_T2 = 2
MODE_T3 = 3
MAXLENCODE = 5
MAXINPCHAN = 2
TTREADMAX = 131072
FLAG_OVERFLOW = 0x0001
FLAG_FIFOFULL = 0x0002

# Measurement parameters, these are hardcoded since this is just a demo
mode = MODE_T2 # set T2 or T3 here, observe suitable Syncdivider and Range!
binning = 0 # you can change this, meaningful only in T3 mode
offset = 0 # you can change this, meaningful only in T3 mode
tacq = 10000 # Measurement time in millisec, you can change this
syncDivider = 1 # you can change this, observe mode! READ MANUAL!
### For TimeHarp 260 P
syncCFDZeroCross = -10 # you can change this (in mV)
syncCFDLevel = -50 # you can change this (in mV)
inputCFDZeroCross = -10 # you can change this (in mV)
inputCFDLevel = -50 # you can change this (in mV)
### For TimeHarp 260 N
syncTriggerEdge = 0 # you can change this
syncTriggerLevel = -50 # you can change this
inputTriggerEdge = 0 # you can change this
inputTriggerLevel = -50 # you can change this

# Variables to store information read from DLLs
buffer = (ct.c_uint * TTREADMAX)()
dev = []
libVersion = ct.create_string_buffer(b"", 8)
hwSerial = ct.create_string_buffer(b"", 8)
hwPartno = ct.create_string_buffer(b"", 8)
hwVersion = ct.create_string_buffer(b"", 16)
hwModel = ct.create_string_buffer(b"", 16)
errorString = ct.create_string_buffer(b"", 40)
numChannels = ct.c_int()
resolution = ct.c_double()
syncRate = ct.c_int()
countRate = ct.c_int()
flags = ct.c_int()
nRecords = ct.c_int()
ctcstatus = ct.c_int()
warnings = ct.c_int()
warningstext = ct.create_string_buffer(b"", 16384)

th260lib = ct.CDLL("th260lib64.dll")

def closeDevices():
    for i in range(0, MAXDEVNUM):
        th260lib.TH260_CloseDevice(ct.c_int(i))
    exit(0)

def stoptttr():
    tryfunc(th260lib.TH260_StopMeas(ct.c_int(dev[0])), "StopMeas")
    closeDevices()

def tryfunc(retcode, funcName, measRunning=False):
    if retcode < 0:
        th260lib.TH260_GetErrorString(errorString, ct.c_int(retcode))
        print("TH260_%s error %d (%s). Aborted." % (funcName, retcode,\
              errorString.value.decode("utf-8")))
        if measRunning:
            stoptttr()
        else:
            closeDevices()


th260lib.TH260_GetLibraryVersion(libVersion)
print("Library version is %s" % libVersion.value.decode("utf-8"))
if libVersion.value.decode("utf-8") != LIB_VERSION:
    print("Warning: The application was built for version %s" % LIB_VERSION)

outputfile = open("tttrmode.out", "wb+")

print("\nSearching for TimeHarp devices...")
print("Devidx     Status")

for i in range(0, MAXDEVNUM):
    retcode = th260lib.TH260_OpenDevice(ct.c_int(i), hwSerial)
    if retcode == 0:
        print("  %1d        S/N %s" % (i, hwSerial.value.decode("utf-8")))
        dev.append(i)
    else:
        if retcode == -1: # TH260_ERROR_DEVICE_OPEN_FAIL
            print("  %1d        no device" % i)
        else:
            th260lib.TH260_GetErrorString(errorString, ct.c_int(retcode))
            print("  %1d        %s" % (i, errorString.value.decode("utf8")))

# In this demo we will use the first TimeHarp device we find, i.e. dev[0].
# You can also use multiple devices in parallel.
# You can also check for specific serial numbers, so that you always know 
# which physical device you are talking to.

if len(dev) < 1:
    print("No device available.")
    closeDevices()
print("Using device #%1d" % dev[0])
print("\nInitializing the device...")

# with internal clock
tryfunc(th260lib.TH260_Initialize(ct.c_int(dev[0]), ct.c_int(mode)), "Initialize")

tryfunc(th260lib.TH260_GetHardwareInfo(dev[0], hwModel, hwPartno, hwVersion),\
        "GetHardwareInfo")
print("Found Model %s Part no %s Version %s" % (hwModel.value.decode("utf-8"),\
      hwPartno.value.decode("utf-8"), hwVersion.value.decode("utf-8")))

tryfunc(th260lib.TH260_GetNumOfInputChannels(ct.c_int(dev[0]), byref(numChannels)),\
        "GetNumOfInputChannels")
print("Device has %i input channels." % numChannels.value)

print("\nUsing the following settings:")
print("Mode              : %d" % mode)
print("Binning           : %d" % binning)
print("Offset            : %d" % offset)
print("AcquisitionTime   : %d" % tacq)
print("SyncDivider       : %d" % syncDivider)

if hwModel.value.decode("utf-8") == "TimeHarp 260 P":
    print("SyncCFDZeroCross  : %d" % syncCFDZeroCross)
    print("SyncCFDLevel      : %d" % syncCFDLevel)
    print("InputCFDZeroCross : %d" % inputCFDZeroCross)
    print("InputCFDLevel     : %d" % inputCFDLevel)
elif hwModel.value.decode("utf-8") == "TimeHarp 260 N":
    print("SyncTriggerEdge   : %d" % syncTriggerEdge)
    print("SyncTriggerLevel  : %d" % syncTriggerLevel)
    print("InputTriggerEdge  : %d" % inputTriggerEdge)
    print("InputTriggerLevel : %d" % inputTriggerLevel)
else:
    print("Unknown hardware model %s. Aborted." % hwModel.value.decode("utf-8"))
    closeDevices()

tryfunc(th260lib.TH260_SetSyncDiv(ct.c_int(dev[0]), ct.c_int(syncDivider)),
        "SetSyncDiv")

if hwModel.value.decode("utf-8") == "TimeHarp 260 P":
    tryfunc(
        th260lib.TH260_SetSyncCFD(ct.c_int(dev[0]), ct.c_int(syncCFDLevel),\
                                      ct.c_int(syncCFDZeroCross)),\
        "SetSyncCFD"
    )
    # we use the same input settings for all channels, you can change this
    for i in range(0, numChannels.value):
        tryfunc(
            th260lib.TH260_SetInputCFD(ct.c_int(dev[0]), ct.c_int(i),\
                                       ct.c_int(inputCFDLevel),\
                                       ct.c_int(inputCFDZeroCross)),\
            "SetInputCFD"
        )

if hwModel.value.decode("utf-8") == "TimeHarp 260 N":
    tryfunc(
        th260lib.TH260_SetSyncEdgeTrg(ct.c_int(dev[0]), ct.c_int(syncTriggerLevel),\
                                      ct.c_int(syncTriggerEdge)),\
        "SetSyncEdgeTrg"
    )
    # we use the same input settings for all channels, you can change this
    for i in range(0, numChannels.value):
        retcode = th260lib.TH260_SetInputEdgeTrg(ct.c_int(dev[0]), ct.c_int(i),\
                                                 ct.c_int(inputTriggerLevel),\
                                                 ct.c_int(inputTriggerEdge))
        if retcode < 0:
            print("TH260_SetInputCFD error %d. Aborted." % retcode)
            closeDevices()

tryfunc(th260lib.TH260_SetSyncChannelOffset(ct.c_int(dev[0]), ct.c_int(0)),\
        "SetSyncChannelOffset")

for i in range(0, numChannels.value):
    tryfunc(
        th260lib.TH260_SetInputChannelOffset(ct.c_int(dev[0]), ct.c_int(i),\
                                             ct.c_int(0)),\
        "SetInputChannelOffset"
    )

tryfunc(th260lib.TH260_SetBinning(ct.c_int(dev[0]), ct.c_int(binning)), "SetBinning")
tryfunc(th260lib.TH260_SetOffset(ct.c_int(dev[0]), ct.c_int(offset)), "SetOffset")
tryfunc(th260lib.TH260_GetResolution(ct.c_int(dev[0]), byref(resolution)),\
        "GetResolution")
print("Resolution is %1.1lfps" % resolution.value)

print("\nMeasuring input rates...")

# Note: after Init or SetSyncDiv allow 150 ms for valid count rate readings
time.sleep(0.15)

tryfunc(th260lib.TH260_GetSyncRate(ct.c_int(dev[0]), byref(syncRate)),
        "GetSyncRate")
print("\nSyncrate=%1d/s" % syncRate.value)

for i in range(0, numChannels.value):
    tryfunc(
        th260lib.TH260_GetCountRate(ct.c_int(dev[0]), ct.c_int(i), byref(countRate)),\
        "GetCountRate"
    )
    print("Countrate[%1d]=%1d/s" % (i, countRate.value))

# after getting the count rates you can check for warnings
tryfunc(th260lib.TH260_GetWarnings(ct.c_int(dev[0]), byref(warnings)), "GetWarnings")
if warnings.value != 0:
    th260lib.TH260_GetWarningsText(ct.c_int(dev[0]), warningstext, warnings)
    print("\n\n%s" % warningstext.value.decode("utf-8"))

print("\nPress RETURN to start")
input()

print("Starting data collection...")

progress = 0
sys.stdout.write("\nProgress:%12u" % progress)
sys.stdout.flush()

tryfunc(th260lib.TH260_StartMeas(ct.c_int(dev[0]), ct.c_int(tacq)), "StartMeas")

while True:
    tryfunc(th260lib.TH260_GetFlags(ct.c_int(dev[0]), byref(flags)), "GetFlags")
    
    if flags.value & FLAG_FIFOFULL > 0:
        print("\nFiFo Overrun!")
        stoptttr()
    
    tryfunc(
        th260lib.TH260_ReadFiFo(ct.c_int(dev[0]), byref(buffer), TTREADMAX,
                                byref(nRecords)),\
        "ReadFiFo", measRunning=True
    )

    if nRecords.value > 0:
        # We could just iterate through our buffer with a for loop, however,
        # this is slow and might cause a FIFO overrun. So instead, we shrinken
        # the buffer to its appropriate length with array slicing, which gives
        # us a python list. This list then needs to be converted back into
        # a ctype array which can be written at once to the output file
        outputfile.write((ct.c_uint*nRecords.value)(*buffer[0:nRecords.value]))
        progress += nRecords.value
        sys.stdout.write("\rProgress:%12u" % progress)
        sys.stdout.flush()
    else:
        tryfunc(th260lib.TH260_CTCStatus(ct.c_int(dev[0]), byref(ctcstatus)),\
                "CTCStatus")
        if ctcstatus.value > 0: 
            print("\nDone")
            stoptttr()
    # within this loop you can also read the count rates if needed.

closeDevices()
outputfile.close()