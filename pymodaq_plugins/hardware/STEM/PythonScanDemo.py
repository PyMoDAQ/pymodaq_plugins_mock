"""
Demo program for class controlling orsay scan hardware.
"""
# standard libraries
import sys
from ctypes import c_void_p, POINTER
from _ctypes import byref, POINTER
import numpy as np
from orsayscan import orsayScan, LOCKERFUNC, UNLOCKERFUNC, UNLOCKERFUNCA


#callback:
SIZEX = 512
SIZEY = 512
SIZEZ = 1

imagedata = np.ones((2*SIZEY*SIZEX,), dtype = np.uint16)
print (imagedata.ctypes.data_as(c_void_p))
#%%
def dataLocker(gene, datatype, sx, sy, sz):
    sx[0] = SIZEX
    sy[0] = SIZEY
    sz[0] = SIZEZ
    datatype[0] = 2
    pointeur = imagedata.ctypes.data_as(c_void_p)
    return pointeur.value


def dataUnlocker(gene, newdata):
    print (imagedata[0:16])

def dataUnlockerA(gene, newdata,  imagenb, rect):
    if newdata:
        print ("Py Image[", gene, "]: ", "image nb: ", imagenb, "   pos: [", rect[0], ", ", rect[1], "]   size: [", rect[2], ", ", rect[3], "]")

#    print ("Scan count: ", orsayscan.getScanCount())
#%%
orsayscan = orsayScan(1)
spimscan = orsayScan(2, orsayscan.orsayscan)

#%%
#def testgeneimage():
orsayscan.externalclock = (0.0, 0.001)
clk = orsayscan.externalclock

nbinputs = orsayscan.getInputsCount()
k = 0
while (k < nbinputs):
    unipolar, offset, name, ind = orsayscan.getInputProperties(k)
    print ("Input:" , k, "   label: ", name, "   video offset: ", offset)
    k = k+1
#orsayscan.OrsayScanSetClock(-1)
#choose X and Y ramps.
orsayscan.SetInputs([6])
nbinputs, inputs = orsayscan.GetInputs()
sizex = SIZEX
sizey = SIZEY
orsayscan.setImageSize(sizex, sizey)
sizex, sizey = orsayscan.getImageSize()
orsayscan.setImageArea(sizex, sizey, 0, sizex, 0, sizey)
res, sx, sy, stx, ex, sty, ey = orsayscan.getImageArea()
print("Pixel time: ", orsayscan.pixelTime)
orsayscan.pixelTime = 0.00002
print("Pixel time: ", orsayscan.pixelTime)

fnlock = LOCKERFUNC(dataLocker)
orsayscan.registerLocker(fnlock)

fnunlock = UNLOCKERFUNCA(dataUnlockerA)
orsayscan.registerUnlockerA(fnunlock)

input("Taper un caractère pour démarrer le scan, puis un autre pour l'arrêter")
orsayscan.startImaging(0, 1)
input("")

orsayscan.stopImaging(1)
#%%
#def testgenespim():
nbinputs = spimscan.getInputsCount()
k = 0
while (k < nbinputs):
    unipolar, offset, name = spimscan.getInputProperties(k)
    print ("Input:" , k, "   label: ", name, "   video offset: ", offset)
    k = k+1
print("Pixel time: ", spimscan.pixelTime)
spimscan.SetInputs([7])
sizex = SIZEX
sizey = SIZEY
spimscan.setImageArea(sizex, sizey, 0, sizex, 0, sizey)
sizex, sizey = spimscan.getImageSize()
res, sx, sy, stx, ex, sty, ey = spimscan.getImageArea()
input("Taper un caractère pour démarrer le scan, puis un autre pour l'arrêter")
# test sur l'entrée eels. (cl = 4)
spimscan.OrsayScanSetClock(2)
#
# simulatation clock camera (tester si le mode simulation est activé sur la caméra et retrouver les 2 paramètres suivants:
camera_simul = True
camera_readout = 0.002
camera_exposure = 0.001
if camera_simul:
    spimscan.OrsayScanSetClockSimulationTime(camera_readout + camera_exposure)
else:
    spimscan.OrsayScanSetClockSimulationTime(0)

spimscan.pixelTime = camera_exposure
spimscan.startImaging(0, 1)
input("")
spimscan.stopImaging(1)


#testgeneimage()
#testgenespim()