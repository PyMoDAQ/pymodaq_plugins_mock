from serial import Serial
from serial.tools.list_ports import comports
import crcmod


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


        ##Get diag 1rt command 0x56
        self.diagnostics = [dict(name='Frequency Mod #1', command=0x30, read=4, unit='Hz', divider=1),
                            dict(name='Osc current', command=0x31, read=2, unit='mA', divider=1),
                            dict(name='Amp current', command=0x32, read=2, unit='A', divider=10),
                            dict(name='Delay Mod #1', command=0x33, read=2, unit='ns', divider=100),
                            dict(name='Width Mod #1', command=0x34, read=4, unit='ns', divider=100),
                            dict(name='Osc Temperature', command=0x35, read=2, unit='Hz', divider=1),
                            dict(name='Amp Temperature', command=0x36, read=2, unit='Hz', divider=1),
                            dict(name='Diode Runtime', command=0x37, read=2, unit='Hz', divider=1),
                            dict(name='Pump Module Temperature', command=0x38, read=2, unit='Hz', divider=1),
                            dict(name='Osc Diode Power', command=0x39, read=2, unit='Hz', divider=1),
                            dict(name='Amp Diode Power', command=0x3A, read=2, unit='', divider=1),
                            dict(name='Osc Laser Power', command=0x3B, read=2, unit='', divider=1),
                            dict(name='Amp Laser Power', command=0x3C, read=2, unit='', divider=1),
                            dict(name='S/N', command=0x3D, read=3, unit='', divider=1),
                            dict(name='HW/SW version', command=0x3E, read=2, unit='', divider=1),
                            dict(name='ID (Broadcast)', command=0x3F, read=1, unit='', divider=1),
                            dict(name='Frequency Mod #2', command=0x40, read=4, unit='', divider=1),
                            dict(name='Delay Mod #2', command=0x41, read=4, unit='', divider=1),
                            dict(name='Width Mod #2', command=0x42, read=4, unit='', divider=1),
                            dict(name='Preamp current', command=0x43, read=2, unit='', divider=1),
                            dict(name='Preamp Diode Power', command=0x44, read=2, unit='', divider=1),
                            dict(name='Preamp Temperature', command=0x45, read=2, unit='', divider=1),
                            dict(name='Preamp Laser Power', command=0x46, read=2, unit='', divider=1),
                            dict(name='Controller Temperature', command=0x47, read=2, unit='', divider=1),
                            dict(name='TPD', command=0x48, read=1, unit='', divider=1),
                            dict(name='Delay Mod #1 coarse', command=0x49, read=4, unit='', divider=1),
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
            self._controller = Serial(com_port)
            # set attributes
            self._controller.baudrate = 115200
            self._controller.bytesize = 8
            self._controller.stopbits = 1
            self._controller.parity = 'N'
            self.timeout = 200
        else:
            raise IOError('{:s} is not a valid port'.format(com_port))

    def close_communication(self):
        self._controller.close()

    def get_status(self):
        """
        Send the "Get Status" command
        The serial port should return 4 bytes encoding the controller status, see self.status
        """

        self._write_command(bytearray([0x53, 0x30]))
        status = self._controller.read(4)  #read 4 bytes
        for dic in self.status:
            dic['value'] = (status[dic['byte']] >> dic['bit']) & 0x01 # check if  corresponding bit in each byte is 0 or 1
        return self.status

    def calc_crc(self, buffer):
        return bytearray(self.crc16.new(buffer).digest())

    def _write_command(self, command, data=[]):
        message = bytearray([self.SYNC, self.STX])
        length = 4 + len(command) + len(data) + 2 #length of the message, excluding the sync byte and including the 2 CRC bytes
        message.append(length)
        message.extend(command)
        message.extend(data)
        message.extend(self.calc_crc(message[1:]))

        self._controller.write(message)

