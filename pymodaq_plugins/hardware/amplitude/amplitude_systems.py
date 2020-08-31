"""
Wrapper around the serial communication protocol for Amplitude Systems lasers

It requires:
pyserial package: pip install pyserial
crcmod package: pip install crcmod (used to certify the message send and received)

"""
from serial import Serial
from serial.tools.list_ports import comports
import crcmod

from pymodaq.daq_utils import daq_utils as utils
logger = utils.set_logger(utils.get_module_name(__file__))

class AmplitudeSystemsCRC16:

    ## set actuator 1st command 0x43
    actuators = [
        dict(id=0, name='Open Shutter', command=0x30, ),
        dict(id=1, name='Close Shutter', command=0x31, ),
        dict(id=2, name='Trigger INT', command=0x32, ),
        dict(id=3, name='Trigger EXT', command=0x33, ),
        dict(id=4, name='Gate INT', command=0x34, ),
        dict(id=5, name='Gate EXT', command=0x35, ),
        dict(id=6, name='Laser ON', command=0x36, ),
        dict(id=7, name='Laser OFF', command=0x37, ),
    ]

    ## Get Status commands 0x53 0x30
    status = [dict(id=0, name='Temp Amp', value=0, byte=0, bit=0x00),
              dict(id=1, name='Temp Osc', value=0, byte=0, bit=0x01),
              dict(id=2, name='Amp Fibre Temp', value=0, byte=0, bit=0x02),
              dict(id=3, name='Supply Connection', value=0, byte=0, bit=0x03),
              dict(id=4, name='Oscillator Instability', value=0, byte=0, bit=0x04),
              dict(id=5, name='Oscillator Stable', value=0, byte=0, bit=0x05),
              dict(id=6, name='Power Drop Error', value=0, byte=0, bit=0x06),
              dict(id=7, name='Power Drop Warning', value=0, byte=0, bit=0x07),

              dict(id=8, name='Front-end Instability', value=0, byte=1, bit=0x00),
              dict(id=9, name='Controller Temp', value=0, byte=1, bit=0x01),
              dict(id=10, name='Preamp Temp', value=0, byte=1, bit=0x02),
              dict(id=11, name='Preamp Current', value=0, byte=1, bit=0x03),
              dict(id=12, name='External', value=0, byte=1, bit=0x04),
              dict(id=13, name='Flow', value=0, byte=1, bit=0x05),
              dict(id=14, name='Amp Current', value=0, byte=1, bit=0x06),
              dict(id=15, name='Osc Current', value=0, byte=1, bit=0x07),

              dict(id=16, name='Osc Status', value=0, byte=2, bit=0x00),
              dict(id=17, name='LD Status', value=0, byte=2, bit=0x01),
              dict(id=18, name='Amp Status', value=0, byte=2, bit=0x02),
              dict(id=19, name='LD Command', value=0, byte=2, bit=0x03),
              dict(id=20, name='Shutter Status', value=0, byte=2, bit=0x04),
              dict(id=21, name='Sync Command', value=0, byte=2, bit=0x05),
              dict(id=22, name='Memory Error', value=0, byte=2, bit=0x06),
              dict(id=23, name='I.Lock Status', value=0, byte=2, bit=0x07),

              dict(id=24, name='FrontEnd Ready', value=0, byte=3, bit=0x00),
              dict(id=25, name='Trigger Option', value=0, byte=3, bit=0x01),
              dict(id=26, name='Preamp Power Drop Error', value=0, byte=3, bit=0x06),

              dict(id=27, name='Frequency Mod2 in range', value=0, byte=4, bit=0x00),
              dict(id=28, name='Delay Mod2 in range', value=0, byte=4, bit=0x01),
              dict(id=29, name='Width Mod2 in range', value=0, byte=4, bit=0x02),
              dict(id=30, name='Frequency Mod1 in range', value=0, byte=4, bit=0x03),
              dict(id=31, name='Delay Mod1 in range', value=0, byte=4, bit=0x04),
              dict(id=32, name='Width Mod1 in range', value=0, byte=4, bit=0x05),
              ]

    ##Get parameter 1rt command 0x56. set parameter: 1rst command 0x54
    diagnostics = [
        dict(id=0, name='Frequency PP', read_command=0x30, write_command=0x30, reply=4, unit='kHz',
             divider=1000, readonly=False, value=-1),
        dict(id=1, name='Osc current', read_command=0x31, write_command=0x31, reply=2, unit='mA', divider=1,
             readonly=False, value=-1),
        dict(id=2, name='Amp current', read_command=0x32, write_command=0x32, reply=2, unit='A', divider=10,
             readonly=False, value=-1),
        dict(id=3, name='Delay PP', read_command=0x33, write_command=0x33, reply=2, unit='ns', divider=100,
             readonly=False, value=-1),
        dict(id=4, name='Width PP', read_command=0x34, write_command=0x34, reply=4, unit='ns', divider=100,
             readonly=False, value=-1),
        dict(id=5, name='Osc Temperature', read_command=0x35, reply=2, unit='°C', divider=10, readonly=True,
             value=-1),
        dict(id=6, name='Amp Temperature', read_command=0x36, reply=2, unit='°C', divider=10, readonly=True,
             value=-1),
        dict(id=7, name='Diode Runtime', read_command=0x37, reply=2, unit='Hours', divider=1, readonly=True,
             value=-1),
        dict(id=8, name='Amplifier Fibre Temperature', read_command=0x38, reply=2, unit='°C', divider=10, readonly=True,
             value=-1),
        dict(id=9, name='Osc Diode Power', read_command=0x39, reply=2, unit='mW', divider=1, readonly=True,
             value=-1),
        # dict(id=10, name='Amp Laser Power', read_command=0x3A, reply=2, unit='W', divider=1, readonly=True,
        #      value=-1),
        # dict(id=11, name='Osc Laser Power', read_command=0x3B, reply=2, unit='mW', divider=1000, readonly=True,
        #      value=-1),
        dict(id=12, name='Amp Laser Power', read_command=0x3C, reply=2, unit='W', divider=1000, readonly=True,
             value=-1),
        dict(id=13, name='S/N', read_command=0x3D, reply=3, unit='', divider=1, readonly=True, value=-1),
        dict(id=14, name='HW/SW version', read_command=0x3E, reply=3, unit='', divider=1, readonly=True, value=-1),
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
        dict(id=25, name='Delay PP coarse', read_command=0x49, write_command=0x3B, reply=4, unit='ns',
             divider=100,
             readonly=False, value=-1),
        dict(id=26, name='SHG Runtime', read_command=0x4A, reply=2, unit='hours', divider=1, readonly=True, value=-1),

        dict(id=27, name='THG runtime', read_command=0x4B, reply=2, unit='hours', divider=1, readonly=True, value=-1),

        dict(id=28, name='Efficiency Mod2', read_command=0x4C, reply=1, unit='%', divider=1, readonly=True, value=-1),
    ]

    def __init__(self, sourceID=0, destID=0x0A):
        super().__init__()
        self._controller = None
        self.com_ports = self.get_ressources()

        self.SYNC = 0x16 #Sync byte
        self.STX = 0x02 #Start byte
        self.message_len_without_data = 9
        self.sourceID = sourceID
        self.destID = destID
        logger.debug(f'Serial object initialized with sourceID {sourceID} and destID {destID}')

        self.crc16 = crcmod.Crc(0x18005, initCrc=0x0000)


    def flush(self):
        self._controller.flush()

    @property
    def timeout(self):
        """
        return serial timeout in ms
        """
        return self._controller.timeout * 1000

    @timeout.setter
    def timeout(self, to):
        """
        Set the serial timeout in ms
        """
        self._controller.timeout = to / 1000

    def get_laser(self):
        return bool(utils.find_dict_in_list_from_key_val(self.status, 'id', 17)['value'])

    def get_shutter(self):
        return bool(utils.find_dict_in_list_from_key_val(self.status, 'id', 20)['value'])

    def set_laser(self, status):
        if status:
            self.set_actuator(6)
        else:
            self.set_actuator(7)

    def set_shutter(self, status):
        if status:
            self.set_actuator(0)
        else:
            self.set_actuator(1)

    def get_sn(self):
        return int.from_bytes(self.get_diag_from_id(13)[0], 'big')

    def get_version(self):

        version = self.get_diag_from_id(14)[0]
        return f'v {version[0]}.{version[1]} {version[2].to_bytes(1,"big").decode()}'

    @classmethod
    def get_ressources(cls):
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
            self.timeout = 200
            self._controller.port = com_port
            self._controller.open()
            logger.debug(f'Serial communication with port {com_port} is a success')
        else:
            raise IOError('{:s} is not a valid port'.format(com_port))

    def close_communication(self):
        logger.debug(f'Serial communication closed')
        try:
            self._controller.close()
        except:
            pass
    def get_status(self):
        """
        Send the "Get Status" command
        The serial port should return 4 bytes encoding the controller status, see self.status

        returns the dicts that have their value changeed
        """

        ret = self._write_command(bytearray([0x53, 0x30]))
        commands, data = self._read_reply(self.message_len_without_data+5) #5 bytes encoding all the infos
        status_changed = []
        for dic in self.status:
            val = (data[dic['byte']] >> dic['bit']) & 0x01  # check if  corresponding bit in each byte is 0 or 1
            if dic['value'] != val:
                dic['value'] = val
                status_changed.append(dic)
        return status_changed

    def get_diag_from_name(self, name):
        diag = utils.find_dict_in_list_from_key_val(self.diagnostics, 'name', name)
        return self.get_diag(diag)

    def get_diag_from_id(self, diag_id):
        diag = utils.find_dict_in_list_from_key_val(self.diagnostics, 'id', diag_id)
        return self.get_diag(diag)

    def get_diag(self, diag):
        data = None
        if diag is not None:
            ret = self._write_command([0x56, diag['read_command']])
            commands, data = self._read_reply(self.message_len_without_data+diag['reply'])
            assert len(data) == diag['reply']
            diag['value'] = int.from_bytes(data, 'big')
        return data, diag

    def set_diag(self, diag_id, value):
        diag = utils.find_dict_in_list_from_key_val(self.diagnostics, 'id', diag_id)
        reply = None
        if diag is not None:
            if not diag['readonly']:
                assert len(value) == diag['reply']
                ret = self._write_command([0x54, diag['write_command']], data=value)
                commands, data = self._read_reply(self.message_len_without_data+diag['reply'])
                assert len(data) == diag['reply']
                diag['value'] = data
        return reply

    def set_actuator(self, actuator_id):
        act = utils.find_dict_in_list_from_key_val(self.actuators, 'id', actuator_id)
        reply = None
        if act is not None:
            ret = self._write_command([0x43, act['command']])
            reply = self._read_reply(self.message_len_without_data)
            self.get_status()

    def calc_crc(self, buffer):
        return bytearray(self.crc16.new(buffer).digest())


    def echo_string(self, string):
        string = string[:min((7, len(string)))]
        ret = self._write_command([0x41, 0x30], data=string.encode())
        commands, data = self._read_reply(ret)
        if commands == bytes([0x41, 0x30]):
            print(f'echo string: {data.decode()}')
        else:
            print('Invalid echo reply')

    def _read_reply(self, Nbytes):
        reply_bytes = self._controller.read(Nbytes)
        if len(reply_bytes) != 0:
            crc = self.calc_crc(reply_bytes[1:-2])
            if crc != reply_bytes[-2:]:
                self._controller.flush()
                raise IOError(f'Invalid message from controller: {reply_bytes}')
            if reply_bytes[3] != self.destID:
                self._controller.flush()
                raise IOError(f'Source of the reply is not correct. Should be {self.destID} but is {reply_bytes[3]}')

            if reply_bytes[4] != self.sourceID:
                self._controller.flush()
                raise IOError(f'Destination of this reply is not meant for this module. Should be {self.sourceID} but is {reply_bytes[4]}')
            commands = reply_bytes[5:7]
            data = reply_bytes[7:-2]
            logger.debug(f'Reply commands: {commands}')
            logger.debug(f'Reply data: {data}')
            return commands, data
        else:
            raise TimeoutError('Read operation on the device returned from a timeout')





    def _write_command(self, command, data=[]):
        message = bytearray([self.SYNC, self.STX])
        length = 4 + len(command) + len(data) + 2 #length of the message, excluding the sync byte and including the 2 CRC bytes
        message.append(length)
        message.extend([self.sourceID, self.destID])
        message.extend(command)
        message.extend(data)
        message.extend(self.calc_crc(message[1:]))
        ret = self._controller.write(message)
        self._controller.flush()
        return ret


if __name__ == '__main__':
    laser = AmplitudeSystemsCRC16(sourceID=0, destID=0x0A)
    com_port = 'COM7'
    laser.init_communication(com_port)
    laser.echo_string('hello')
    laser.get_status()
    laser.get_diag(0)
    laser.close_communication()