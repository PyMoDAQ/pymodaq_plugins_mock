import ctypes
import os
import re

"""
Smaract dll declaration followed by the functions prototyping
doc at : C:\SmarAct\MCS\Documentation
MCS Programmers Guide.pdf is very complete

We suppose to work with Windows OS

The support of multiple controllers connected to the machine has to be tested
"""

# We suppose the .dll library is in the same directory
# The CDLL function asks for the full path
# We suppose to work with Windows OS
dir_path = os.path.dirname(os.path.realpath(__file__))
SmaractDll = ctypes.CDLL(dir_path + "\MCSControl.dll")

# prototype of the SA_FindSystems function
# uint32_t SA_FindSystems(const CStr options, CStr outList, uint32_t *ioListSize);
SmaractDll.SA_FindSystems.argtypes = [
    ctypes.POINTER(ctypes.c_char),  # Parameter 1
    ctypes.c_char_p,  # Parameter 2
    ctypes.POINTER(ctypes.c_ulong)]  # Parameter 3
SmaractDll.SA_FindSystems.restype = ctypes.c_ulong


class SmarAct(object):

    def __init__(self):
        super(SmarAct, self).__init__()

        self.controller_locator = self.get_controller_locator()

    # get the locator (e.g. usb:id:3118167233) of the plugged MCS controller
    # we suppose that only one is connected
    def get_controller_locator(self):
        ioListSize = 4096
        options = ctypes.c_char()
        outList = (' ' * ioListSize).encode()
        ioListSize = ctypes.c_ulong(ioListSize)

        status = SmaractDll.SA_FindSystems(
            ctypes.byref(options),
            outList,
            ctypes.byref(ioListSize)
        )

        if status != 0:
            raise Exception('SmarAct SA_FindSystems error')

        system_locator = re.findall("usb:id:[0-9]{10}", outList.decode())

        if not system_locator:
            raise Exception('No controller found')

        return system_locator
