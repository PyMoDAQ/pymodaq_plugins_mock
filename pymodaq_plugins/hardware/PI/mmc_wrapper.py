import sys
from ctypes import windll, create_string_buffer, POINTER, byref, pointer
from ctypes import c_uint, c_int, c_char, c_char_p, c_void_p, c_short, c_long, c_bool, c_double, c_uint64, c_uint32, Array, CFUNCTYPE, WINFUNCTYPE
from ctypes import c_ushort, c_ulong, c_float
import os
from visa import ResourceManager
from bitstring import Bits

class MMC_Wrapper(object):
    """
    Wrapper to the MMC dll from Physik Instrumente

    """
    stages = {'M521DG': dict(cts_units_num=2458624, cts_units_denom=81, units="mm")}
    VISA_rm = ResourceManager()
    ress = VISA_rm.list_resources_info()
    aliases = []
    ports = []
    for key in ress.keys():
        if 'COM' in ress[key].alias:
            aliases.append(ress[key].alias)
            ports.append(ress[key].interface_board_number)

    baudrates = [9600, 19200]

    def __init__(self,stage='M521DG', com_port='COM1', baud_rate=9600):
        if stage not in self.stages.keys():
            raise Exception('not valid stage')
        if com_port not in self.aliases:
            raise IOError('invalid com port')
        if baud_rate not in self.baudrates:
            raise IOError('invalid baudrate')
        self.stage = stage
        super(MMC_Wrapper,self).__init__()
        self._comport = com_port
        self._baudrate = baud_rate
        self._dll = windll.LoadLibrary(os.path.join(os.path.split(__file__)[0],'MMC.dll'))

    @property
    def comport(self):
        return self._comport

    @comport.setter
    def comport(self,port):
        if not isinstance(port, str):
            raise TypeError("not a valid port type, should be a string: 'COM6'")
        if port not in self.ports:
            raise IOError('{} is an invalid COM port'.format(port))
        self._comport = port

    @property
    def baudrate(self):
        return self._comport

    @baudrate.setter
    def baudrate(self,rate):
        if not isinstance(rate, int):
            raise TypeError("not a valid baudrate")
        if rate not in self.baudrates:
            raise IOError('{} is an invalid baudrate'.format(rate))
        self._baudrate = rate

    def counts_to_units(self,counts):
        return counts*1/(self.stages[self.stage]['cts_units_num']/self.stages[self.stage]['cts_units_denom'])

    def units_to_counts(self,units):
        return int(units/(self.stages[self.stage]['cts_units_denom']/self.stages[self.stage]['cts_units_num']))

    def moveAbs(self,axis, units):
        """
        displacement in the selected stage units
        Parameters
        ----------
        units: (float)
        """
        self.MMC_moveA(axis, self.units_to_counts(units))

    def moveRel(self,axis, units):
        """
        displacement in the selected stage units
        Parameters
        ----------
        units: (float)
        """
        self.MMC_moveR(axis, self.units_to_counts(units))

    def getPos(self):
        return self.counts_to_units(self.MMC_getPos())

    def open(self):
        port = self.ports[self.aliases.index(self._comport)]
        self.MMC_COM_open(port,self._baudrate)

    def find_home(self):
        self.MMC_sendCommand('FE1')

    def moving(self):
        target = self.MMC_getVal(2)
        self.MMC_sendCommand('TE')
        st = self.MMC_getStringCR()
        if '-' in st:
            pos = -int(st.split('E:-')[1])
        else:
            pos = int(st.split('E:+')[1])
        return abs(target - pos) > 100

    def MMC_getStringCR(self):
        st = create_string_buffer(128)
        res = self._dll.MMC_getStringCR(byref(st))
        if res != 0:
            return st.decode()
        else:
            raise IOError('wrong return from dll')

    def MMC_COM_open(self, port_number, baudrate):
        res = self._dll.MMC_COM_open(port_number, baudrate)
        if res != 0:
            raise IOError('wrong return from dll')

    def MMC_COM_close(self):
        """
        Closes the COM port previously opened by the MMC_COM_open function.

        """
        res = self._dll.MMC_COM_close()
        if res != 0:
            raise IOError('wrong return from dll')

    def MMC_COM_EOF(self):
        """
        Returns the number of characters available in the COM-port input buffer
        Returns
        -------
        int: Number of characters in the input buffer
        """
        res = self._dll.MMC_COM_EOF()
        return res

    def MMC_COM_clear(self):
        """
        Clears the COM-port input buffer.
        """
        res = self._dll.MMC_COM_clear()
        if res != 0:
            raise IOError('wrong return from dll')



    def MMC_getDLLversion(self):
        """
        Delivers the version number of the DLL
        Returns
        -------
        int: version number as integer

        """
        res = self._dll.MMC_getDLLversion()
        return res


    def MMC_getPos(self):
        """
        Reads the current motor position of the currently selected Mercury™ controller.
        The reading process does not interrupt running compound commands.
        Returns
        -------
        int:    Current motor position in counts/steps or error code.
                The error code is derived from maximum integer value minus the error number:
                2,147,483,647 (maxint) : Wrong Content
                2,147,483,646 (maxint-1) : Error in _getString
                2,147,483,645 (maxint-2) : Error in _sendString
                2,147,483,644 (maxint-3) : Error during conversion
        """
        res = self._dll.MMC_getPos()
        return res

    def MDC_getPosErr(self):
        """
        Reads the current motor-position error of the currently selected Mercury™ controller.
        Returns
        -------
        int:    Current motor position error in counts or error code.
                The error code is derived from maximum integer value minus the error number:
                2,147,483,647 (maxint) : Wrong Content
                2,147,483,646 (maxint-1) : Error in _getString
                2,147,483,645 (maxint-2) : Error in _sendString
                2,147,483,644 (maxint-3) : Error during conversion
        """

        res = self._dll.MDC_getPosErr()
        return res

    def MMC_getVal(self, command_ID: int):
        """
        Reads the value of the requested parameter.
        The function can be called on the fly. Running compound commands or macros are not interrupted.
        Parameters
        ----------
        command_ID: (int) Identifier for the requested item:
                            1 = TP (Tell Position)
                            2 = TT (Tell Target)
                            3 = TF (Tell profile following error)
                            4 = TE (Tell distance to target)
                            5 = TY (Tell velocity setting)
                            6 = TL (Tell acceleration setting)
                            7 = GP (Get p-term setting)
                            8 = GI (Get i-term setting)
                            9 = GD (Get d-term setting)
                            10 = GL (Get i-limit setting)
        Returns
        -------
        int: The requested value or error code is returned as 32-bit integer.
                Error codes:
                2,147,483,647 (MaxInt) = content error
                2,147,483,646 (MaxInt-1) = getString error
                2,147,483,645 (MaxInt-2) = sendString error
                2,147,483,644 (MaxInt-3) = conversion error
        """
        res = self._dll.MMC_getVal(command_ID)
        return res

    def MMC_initNetwork(self, maxAxis: int=16):
        """
        Searches all addresses, starting at address maxAxis down to 1 for Mercury™ devices connected.
        If a Mercury™ device (can be C-862, C-863, C-663 or C-170) is found, it is registered so as to allow access through the MMC_select() function.
        The function MMC_initNetwork is optional. If it is not used, devices can be activated anyway using the MMC_setDevice function.
        Parameters
        ----------
        maxAxis: (int) This parameter represents the highest device number from which the search is to run, continuing downwards.
                        If you have 3 Mercury™s connected at the addresses 0,1 and 2 (this equals the device numbers 1,2 and 3) you may call the function as MMC_initNetwork(3).
                        If you do no know what addresses the controllers are set to, call the function with maxAxis = 16 to find all devices connected. (Remember that valid device numbers range from 1 to 16.)
                        The range of maxAxis is 1 to 16
                        Because scanning each address takes about 0.5 seconds, it saves time to not start at device numbers higher than required.
        Returns
        -------
        list: list of integers corresponding to the connected devices
        """
        devices = []
        res = self._dll.MMC_initNetwork(maxAxis)
        if res < 0:
            raise IOError('wrong return from dll')
        if res > 0:
            bits = Bits(int=res, length=32).bin
            for ind in range(maxAxis):
                if bits[-1-ind] == '1':
                    devices.append(ind+1)
        return devices

    def MMC_moveA(self, axis: int=0, position: int=0):
        """
        Moves the motor of the specified axis (device number) to specified position.
        Parameters
        ----------
        axis: (int) If this parameter is 0 then the move command is sent to the currently selected device.
                    If it is >0 then an address selection code will be sent for the specified axis addressed
                    before the move command is sent.
        position: (int) The new target position

        Returns
        -------
        int:    Error codes:
                    0: No error
                    1: Error, wrong axis
                    2: Error, not connected
                    3: Error, sendString
        """
        res = self._dll.MMC_moveA(axis, position)
        return res

    def MMC_moveR(self, axis: int=0, shift: int=0):
        """
        Moves the motor of the specified axis (device number) relative to its current position by shift counts or steps.
        Parameters
        ----------
        axis: (int) If this parameter is 0 then the move command is sent to the currently selected device.
                    If it is >0 then an address selection code will be sent for the specified axis before
                    the move command is sent.
        shift: (int) Position increment added to the current position.
        Returns
        -------
        int:    Error codes:
                    0: No error
                    1: Error, wrong axis
                    2: Error, not connected
                    3: Error, sendString
        """
        res = self._dll.MMC_moveR(axis, shift)
        return res

        
        
    def MDC_moving(self):
        """
        Returns the motion status of the currently selected C-862 or C-863 Mercury™ DC motor controller.
        For C-663 Mercury™-Step controllers, an equivalent function is available.
        Returns
        -------
        bool: moving status
                    0: Not moving
                    1: moving
        """
        res = self._dll.MDC_moving()
        if res < 0:
            raise IOError('wrong return from dll')
        else:
            return bool(res)

    def MST_moving(self):
        """
        Returns the moving status of the currently selected Mercury™-Step controller.
        For Mercury™ DC motor controllers, an equivalent function is available.
        Returns
        -------
        bool: moving status
                    0: Not moving
                    1: moving
        """
        res = self._dll.MST_moving()
        if res < 0:
            raise IOError('wrong return from dll')
        else:
            return bool(res)
    
    def MMC_setDevice(self, axis: int=0):
        """
        Addresses the selected axis (controller).
        This function works anytime and it is not required to have registered the devices connected with the MMC_intNetwork function.
        See also
        --------
        MMC_select()
        Parameters
        ----------
        axis: (int) Range 1 to 16,
                Device number of the controller that shall be selected for communication.
                The device number or address can be set by the controller's front panel DIP switches.
        """
        res = self._dll.MMC_setDevice(axis)
        if res ==1:
            raise IOError('Wrong axis number')

    def MMC_select(self, axis: int=0):
        """
        Selects the specified axis (device) to enable communication with it.
        Unlike the MMC_setDevice function, here the registration status is checked, so this function requires that the
        MMC_initNetwork function have been called previously at the beginning of the program.
        Parameters
        ----------
        axis: (int) range 1 to 16 Device number of the controller that is to be selected for communication.
        """
        res = self._dll.MMC_select(axis)
        if res == 1:
            raise IOError('Wrong axis number')
        elif res == 2:
            raise IOError('axis not registered')

    def MMC_sendCommand(self,cmd):
        c_cmd = create_string_buffer(cmd.encode())
        res = self._dll.MMC_sendCommand(byref(c_cmd))
        if res == 114:
            raise IOError('Write error')
        elif res == 116:
            raise IOError('Length Error')


    def MDC_waitStop(self):
        """
        For C-862 Mercury™ (DC motor) C-863 Mercury™ (DC motor)
        Waits until the current move has terminated or interrupted by user command (function MCC_GlobalBreak).
        """
        res = self._dll.MDC_waitStop()
        if res == 1:
            raise IOError('Error, query')
        elif res == 2:
            raise IOError('User break')

    def MST_waitStop(self):
        """
        For C-663 Mercury™-Step
        Waits until the current move has terminated or interrupted by user command (function MCC_GlobalBreak).
        """
        res = self._dll.MST_waitStop()
        if res == 1:
            raise IOError('Error, query')
        elif res == 2:
            raise IOError('User break')

    def MMC_globalBreak(self):
        """
        This function interrupts pending operations waiting for termination of a move. Can be used with _moving()
        or _waitStop functions.

        """
        res = self._dll.MMC_globalBreak()
        if res != 0:
            raise IOError('wrong return from dll')
