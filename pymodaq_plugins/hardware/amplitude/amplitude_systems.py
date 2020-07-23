from serial import Serial
from serial.tools.list_ports import comports
import crcmod

from pymodaq.daq_utils import daq_utils as utils

class AmplitudeSystemsCRC16:

    def __init__(self, sourceID=0, destID=0x0A):
        super().__init__()
        self._controller = None
        self.com_ports = self.get_ressources()

        self.SYNC = 0x16 #Sync byte
        self.STX = 0x02 #Start byte
        self.sourceID = sourceID
        self.destID = destID

        self.crc16 = crcmod.Crc(0x18005, initCrc=0x0000)

        ## set actuator 1st command 0x43
        self.actuators = [
            dict(id=0, name='Open Shutter', command=0x30,),
            dict(id=1, name='Close Shutter', command=0x31, ),
            dict(id=2, name='Trigger INT', command=0x32, ),
            dict(id=3, name='Trigger EXT', command=0x33, ),
            dict(id=4, name='Gate INT', command=0x34, ),
            dict(id=5, name='Gate EXT', command=0x35, ),
            dict(id=6, name='Laser ON', command=0x36, ),
            dict(id=7, name='Laser OFF', command=0x37, ),
        ]

        ## Get Status commands 0x53 0x30
        self.status = [dict(name='Temp Amp', value=0, byte=0, bit=0x00),
                       dict(name='Temp Osc', value=0, byte=0, bit=0x01),
                       dict(name='Supply Connection', value=0, byte=0, bit=0x03),
                       dict(name='Oscillator Instability', value=0, byte=0, bit=0x04),
                       dict(name='Oscillator Stable', value=0, byte=0, bit=0x05),
                       dict(name='Power Drop Error', value=0, byte=0, bit=0x06),

                       dict(name='Front-end Instability', value=0, byte=1, bit=0x00),
                       dict(name='Controller Temp', value=0, byte=1, bit=0x01),
                       dict(name='Preamp Temp', value=0, byte=1, bit=0x02),
                       dict(name='Preamp Current', value=0, byte=1, bit=0x03),
                       dict(name='External', value=0, byte=1, bit=0x04),
                       dict(name='Flow', value=0, byte=1, bit=0x05),
                       dict(name='Amp Current', value=0, byte=1, bit=0x06),
                       dict(name='Osc Current', value=0, byte=1, bit=0x07),

                       dict(name='Osc Status', value=0, byte=2, bit=0x00),
                       dict(name='LD Status', value=0, byte=2, bit=0x01),
                       dict(name='Amp Status', value=0, byte=2, bit=0x02),
                       dict(name='LD Command', value=0, byte=2, bit=0x03),
                       dict(name='Shutter Status', value=0, byte=2, bit=0x04),
                       dict(name='Sync Command', value=0, byte=2, bit=0x05),
                       dict(name='I.Lock Status', value=0, byte=2, bit=0x07),
                       ]


        ##Get parameter 1rt command 0x56. set parameter: 1rst command 0x54 
        self.diagnostics = [
            dict(id=0, name='Frequency Mod #1', read_command=0x30, write_command=0x30, reply=4, unit='kHz',
                 divider=1000, readonly=False, value=-1),
            dict(id=1, name='Osc current', read_command=0x31, write_command=0x31, reply=2, unit='mA', divider=1,
                 readonly=False, value=-1),
            dict(id=2, name='Amp current', read_command=0x32, write_command=0x32, reply=2, unit='A', divider=10,
                 readonly=False, value=-1),
            dict(id=3, name='Delay Mod #1', read_command=0x33, write_command=0x33, reply=2, unit='ns', divider=100,
                 readonly=False, value=-1),
            dict(id=4, name='Width Mod #1', read_command=0x34, write_command=0x34, reply=4, unit='ns', divider=100,
                 readonly=False, value=-1),
            dict(id=5, name='Osc Temperature', read_command=0x35, reply=2, unit='°C', divider=10, readonly=True,
                 value=-1),
            dict(id=6, name='Amp Temperature', read_command=0x36, reply=2, unit='°C', divider=10, readonly=True,
                 value=-1),
            dict(id=7, name='Diode Runtime', read_command=0x37, reply=2, unit='Hours', divider=1, readonly=True,
                 value=-1),
            dict(id=8, name='Pump Module Temperature', read_command=0x38, reply=2, unit='°C', divider=10, readonly=True,
                 value=-1),
            dict(id=9, name='Osc Diode Power', read_command=0x39, reply=2, unit='mW', divider=1, readonly=True,
                 value=-1),
            dict(id=10, name='Amp Diode Power', read_command=0x3A, reply=2, unit='W', divider=1, readonly=True,
                 value=-1),
            dict(id=11, name='Osc Laser Power', read_command=0x3B, reply=2, unit='mW', divider=1000, readonly=True,
                 value=-1),
            dict(id=12, name='Amp Laser Power', read_command=0x3C, reply=2, unit='W', divider=1000, readonly=True,
                 value=-1),
            dict(id=13, name='S/N', read_command=0x3D, reply=3, unit='', divider=1, readonly=True, value=-1),
            dict(id=14, name='HW/SW version', read_command=0x3E, reply=2, unit='', divider=1, readonly=True, value=-1),
            dict(id=15, name='ID (Broadcast)', read_command=0x3F, reply=1, unit='', divider=1, readonly=True, value=-1),
            dict(id=16, name='Frequency Mod #2', read_command=0x40, write_command=0x35, reply=4, unit='kHz',
                 divider=1000,
                 readonly=False, value=-1),
            dict(id=17, name='Delay Mod #2', read_command=0x41, write_command=0x37, reply=4, unit='ns', divider=100,
                 readonly=False, value=-1),
            dict(id=18, name='Width Mod #2', read_command=0x42, write_command=0x36, reply=4, unit='ns', divider=100,
                 readonly=False, value=-1),
            dict(id=19, name='Preamp current', read_command=0x43, write_command=0x38, reply=2, unit='mA', divider=1,
                 readonly=False, value=-1),
            dict(id=20, name='Preamp Diode Power', read_command=0x44, reply=2, unit='mW', divider=1, readonly=True,
                 value=-1),
            dict(id=21, name='Preamp Temperature', read_command=0x45, reply=2, unit='°C', divider=10, readonly=True,
                 value=-1),
            dict(id=22, name='Preamp Laser Power', read_command=0x46, reply=2, unit='mW', divider=100, readonly=True,
                 value=-1),
            dict(id=23, name='Controller Temperature', read_command=0x47, reply=2, unit='°C', divider=10, readonly=True,
                 value=-1),
            dict(id=24, name='TPD', read_command=0x48, reply=1, unit='', divider=1, readonly=True, value=-1),
            dict(id=25, name='Delay Mod #1 coarse', read_command=0x49, write_command=0x3B, reply=4, unit='ns',
                 divider=100,
                 readonly=False, value=-1),
            ]

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, to):
        self._timeout = to
        self._controller.timeout = to

    def get_ressources(self):
        infos = comports()
        com_ports = [info.device for info in infos]
        return com_ports

    def init_communication(self, com_port):
        if com_port in self.com_ports:
            self._controller = Serial()
            # set attributes
            self._controller.baudrate = 115200
            self._controller.bytesize = 8
            self._controller.stopbits = 1
            self._controller.parity = 'N'
            self.timeout = 200 / 1000
            self._controller.port = com_port
            self._controller.open()
        else:
            raise IOError('{:s} is not a valid port'.format(com_port))

    def close_communication(self):
        self._controller.close()

    def get_status(self):
        """
        Send the "Get Status" command
        The serial port should return 4 bytes encoding the controller status, see self.status

        returns the dicts that have their value changeed
        """

        ret= self._write_command(bytearray([0x53, 0x30]))
        status = self._read_reply(4)  #read 4 bytes
        status_changed = []
        for dic in self.status:
            val = (status[dic['byte']] >> dic['bit']) & 0x01  # check if  corresponding bit in each byte is 0 or 1
            if dic['value'] != val:
                dic['value'] = val
                status_changed.append(dic)
        return status_changed

    def get_diag(self, diag_id):
        diag = utils.find_dict_in_list_from_key_val(self.diagnostics, 'id', diag_id)
        reply = None
        if diag is not None:
            ret = self._write_command([0x56, diag['read_command']])

            reply = self._read_reply(diag['reply'])
            diag['value'] = reply
        return reply

    def set_diag(self, diag_id, value):
        diag = utils.find_dict_in_list_from_key_val(self.diagnostics, 'id', diag_id)
        reply = None
        if diag is not None:
            if not diag['readonly']:
                assert len(value) == diag['reply']
                self._write_command([0x54, diag['write_command']], data=value)

            reply = self._read_reply(diag['reply'])
            diag['value'] = reply
        return reply

    def set_actuator(self, actuator_id):
        act = utils.find_dict_in_list_from_key_val(self.actuators, 'id', actuator_id)
        reply = None
        if act is not None:
            self._write_command([0x43, act['command']])
            self.get_status()

    def calc_crc(self, buffer):
        return bytearray(self.crc16.new(buffer).digest())


    def echo_string(self, string):
        string = string[:min((7, len(string)))]
        ret = self._write_command([0x41, 0x30], data=string.encode())
        self._read_reply(len(string))

    def _read_reply(self, Nbytes):
        #TODO check if the reply contains also the SYNC, STX, COMMAND DATA and CRC...
        reply_bytes = self._controller.read(Nbytes)
        return int.from_bytes(reply_bytes, 'big')

    def _write_command(self, command, data=[]):
        message = bytearray([self.SYNC, self.STX])
        length = 4 + len(command) + len(data) + 2 #length of the message, excluding the sync byte and including the 2 CRC bytes
        message.append(length)
        message.extend([self.sourceID, self.destID])
        message.extend(command)
        message.extend(data)
        message.extend(self.calc_crc(message[1:]))
        ret = self._controller.write(message)
        return ret


if __name__ == '__main__':
    laser = AmplitudeSystemsCRC16(sourceID=0, destID=0x0A)
    com_port = 'COM6'
    laser.init_communication(com_port)
    laser.echo_string('hello')
    pass