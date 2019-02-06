# Demo for access to TimeHarp 260 Hardware via TH260LIB.DLL v 3.1.
# The program performs a measurement based on hard coded settings.
# The resulting histogram is stored in an ASCII output file.
#
# Keno Goertz, PicoQuant GmbH, February 2018

import time
import ctypes as ct
from ctypes import byref

# From th260defin.h
LIB_VERSION = "3.1"
MAXDEVNUM = 4
MODE_HIST = 0
MAXLENCODE = 5
MAXINPCHAN = 2
MAXHISTLEN = 32768
FLAG_OVERFLOW = 0x0001

# Measurement parameters, these are hardcoded since this is just a demo
binning = 0 # you can change this
offset = 0
tacq = 1000 # Measurement time in millisec, you can change this
syncDivider = 1 # you can change this 
### For TimeHarp 260 P
syncCFDZeroCross = -10 # you can change this
syncCFDLevel = -50 # you can change this
inputCFDZeroCross = -10 # you can change this
inputCFDLevel = -50 # you can change this
### For TimeHarp 260 N
syncTriggerEdge = 0 # you can change this
syncTriggerLevel = -50 # you can change this
inputTriggerEdge = 0 # you can change this
inputTriggerLevel = -50 # you can change this

# Variables to store information read from DLLs
counts = [(ct.c_uint * MAXHISTLEN)() for i in range(0, MAXINPCHAN)]
dev = []
libVersion = ct.create_string_buffer(b"", 8)
hwSerial = ct.create_string_buffer(b"", 8)
hwPartno = ct.create_string_buffer(b"", 8)
hwVersion = ct.create_string_buffer(b"", 16)
hwModel = ct.create_string_buffer(b"", 16)
errorString = ct.create_string_buffer(b"", 40)
numChannels = ct.c_int()
histLen = ct.c_int()
resolution = ct.c_double()
syncRate = ct.c_int()
countRate = ct.c_int()
flags = ct.c_int()
warnings = ct.c_int()
warningstext = ct.create_string_buffer(b"", 16384)
cmd = 0

th260lib = ct.CDLL("th260lib64.dll")

def closeDevices():
    for i in range(0, MAXDEVNUM):
        th260lib.TH260_CloseDevice(ct.c_int(i))
    exit(0)

def tryfunc(retcode, funcName):
    if retcode < 0:
        th260lib.TH260_GetErrorString(errorString, ct.c_int(retcode))
        print("TH260_%s error %d (%s). Aborted." % (funcName, retcode,\
              errorString.value.decode("utf-8")))
        closeDevices()

th260lib.TH260_GetLibraryVersion(libVersion)
print("Library version is %s" % libVersion.value.decode("utf-8"))
if libVersion.value.decode("utf-8") != LIB_VERSION:
    print("Warning: The application was built for version %s" % LIB_VERSION)

outputfile = open("histomode.out", "w+")

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

outputfile.write("Binning           : %d\n" % binning)
outputfile.write("Offset            : %d\n" % offset)
outputfile.write("AcquisitionTime   : %d\n" % tacq)
outputfile.write("SyncDivider       : %d\n" % syncDivider)

print("\nInitializing the device...")

# Histo mode with internal clock
tryfunc(th260lib.TH260_Initialize(ct.c_int(dev[0]), ct.c_int(MODE_HIST)),\
        "Initialize")

tryfunc(th260lib.TH260_GetHardwareInfo(dev[0], hwModel, hwPartno, hwVersion),\
        "GetHardwareInfo")
print("Found Model %s Part no %s Version %s" % (hwModel.value.decode("utf-8"),\
      hwPartno.value.decode("utf-8"), hwVersion.value.decode("utf-8")))

if hwModel.value.decode("utf-8") == "TimeHarp 260 P":
    outputfile.write("SyncCFDZeroCross  : %d\n" % syncCFDZeroCross)
    outputfile.write("SyncCFDLevel      : %d\n" % syncCFDLevel)
    outputfile.write("InputCFDZeroCross : %d\n" % inputCFDZeroCross)
    outputfile.write("InputCFDLevel     : %d\n" % inputCFDLevel)
elif hwModel.value.decode("utf-8") == "TimeHarp 260 N":
    outputfile.write("SyncTriggerEdge   : %d\n" % syncTriggerEdge)
    outputfile.write("SyncTriggerLevel  : %d\n" % syncTriggerLevel)
    outputfile.write("InputTriggerEdge  : %d\n" % inputTriggerEdge)
    outputfile.write("InputTriggerLevel : %d\n" % inputTriggerLevel)
else:
    print("Unknown hardware model %s. Aborted." % hwModel.value.decode("utf-8"))
    closeDevices()

tryfunc(th260lib.TH260_GetNumOfInputChannels(ct.c_int(dev[0]), byref(numChannels)),\
        "GetNumOfInputChannels")
print("Device has %i input channels." % numChannels.value)

tryfunc(th260lib.TH260_SetSyncDiv(ct.c_int(dev[0]), ct.c_int(syncDivider)),\
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
        tryfunc(
            th260lib.TH260_SetInputEdgeTrg(ct.c_int(dev[0]), ct.c_int(i),\
                                           ct.c_int(inputTriggerLevel),\
                                           ct.c_int(inputTriggerEdge)),\
            "SetInputEdgeTrg"
        )

tryfunc(th260lib.TH260_SetSyncChannelOffset(ct.c_int(dev[0]), ct.c_int(0)),\
        "SetSyncChannelOffset")

for i in range(0, numChannels.value):
    tryfunc(
        th260lib.TH260_SetInputChannelOffset(ct.c_int(dev[0]), ct.c_int(i),\
                                             ct.c_int(0)),\
        "SetInputChannelOffset"
    )

tryfunc(
    th260lib.TH260_SetHistoLen(ct.c_int(dev[0]), ct.c_int(MAXLENCODE), byref(histLen)),\
    "SetHistoLen"
)
print("Histogram length is %d" % histLen.value)

tryfunc(th260lib.TH260_SetBinning(ct.c_int(dev[0]), ct.c_int(binning)), "SetBinning")
tryfunc(th260lib.TH260_SetOffset(ct.c_int(dev[0]), ct.c_int(offset)), "SetOffset")
tryfunc(th260lib.TH260_GetResolution(ct.c_int(dev[0]), byref(resolution)),\
        "GetResolution")
print("Resolution is %1.1lfps" % resolution.value)

# Note: after Init or SetSyncDiv allow 150 ms for valid  count rate readings
# Otherwise you get new values after every 100ms
time.sleep(0.15)

tryfunc(th260lib.TH260_GetSyncRate(ct.c_int(dev[0]), byref(syncRate)), "GetSyncRate")
print("\nSyncrate=%1d/s" % syncRate.value)

for i in range(0, numChannels.value):
    tryfunc(th260lib.TH260_GetCountRate(ct.c_int(dev[0]), ct.c_int(i), byref(countRate)),\
            "GetCountRate")
    print("Countrate[%1d]=%1d/s" % (i, countRate.value))

# after getting the count rates you can check for warnings
tryfunc(th260lib.TH260_GetWarnings(ct.c_int(dev[0]), byref(warnings)), "GetWarnings")
if warnings.value != 0:
    th260lib.TH260_GetWarningsText(ct.c_int(dev[0]), warningstext, warnings)
    print("\n\n%s" % warningstext.value.decode("utf-8"))

tryfunc(th260lib.TH260_SetStopOverflow(ct.c_int(dev[0]), ct.c_int(0), ct.c_int(10000)),\
        "SetStopOverflow") # for example only

while cmd != "q":
    tryfunc(th260lib.TH260_ClearHistMem(ct.c_int(dev[0])), "ClearHistMem")

    print("press RETURN to start measurement")
    input()

    tryfunc(th260lib.TH260_GetSyncRate(ct.c_int(dev[0]), byref(syncRate)),\
            "GetSyncRate")
    print("Syncrate=%1d/s" % syncRate.value)

    for i in range(0, numChannels.value):
        tryfunc(
            th260lib.TH260_GetCountRate(ct.c_int(dev[0]), ct.c_int(i),\
                                        byref(countRate)),\
            "GetCountRate"
        )
        print("Countrate[%1d]=%1d/s" % (i, countRate.value))

    # here you could check for warnings again
    
    tryfunc(th260lib.TH260_StartMeas(ct.c_int(dev[0]), ct.c_int(tacq)), "StartMeas")
    print("\nMeasuring for %1d milliseconds..." % tacq)
    
    ctcstatus = ct.c_int(0)
    while ctcstatus.value == 0:
        tryfunc(th260lib.TH260_CTCStatus(ct.c_int(dev[0]), byref(ctcstatus)),\
                "CTCStatus")
        
    tryfunc(th260lib.TH260_StopMeas(ct.c_int(dev[0])), "StopMeas")
    
    for i in range(0, numChannels.value):
        tryfunc(
            th260lib.TH260_GetHistogram(ct.c_int(dev[0]), byref(counts[i]),\
                                        ct.c_int(i), ct.c_int(0)),\
            "GetHistogram"
        )
        integralCount = 0
        for j in range(0, histLen.value):
            integralCount += counts[i][j]
        print("  Integralcount[%1d]=%1.0lf" % (i,integralCount))

    tryfunc(th260lib.TH260_GetFlags(ct.c_int(dev[0]), byref(flags)), "GetFlags")
    
    if flags.value & FLAG_OVERFLOW > 0:
        print("  Overflow.")

    print("Enter c to continue or q to quit and save the count data.")
    cmd = input()

for j in range(0, histLen.value):
    for i in range(0, numChannels.value):
        outputfile.write("%5d " % counts[i][j])
    outputfile.write("\n")

closeDevices()
outputfile.close()