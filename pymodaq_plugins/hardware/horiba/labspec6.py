import socket
import numpy as np

COMMANDS = {'GetRamanParam': 'param',
            'SetRamanParameter': 'param',
            'EnableSpectralResponse': 'array',
            'SetPointList': 'array',
            'SetActivePoint': 'array',
            'StartRamanMeasurement': 'array',
            'SetRamanParams': 'array',
            'Logout': None
            }

PARAMS = {'AcquisitionTime': {'tip': 'Approximate total Acquisition time in seconds', 'get_set': 'get'},
          'Exposure': {'tip': 'Exposure time in seconds', 'get_set': 'set'},
          'Accumulations': {'tip': 'Exposure time in seconds', 'get_set': 'set'},
          'LaserWavelength': {'tip': 'Current laser wavelength in nm', 'get_set': 'get'},
          'Binning': {'tip': 'Xaxis binning', 'get_set': 'both'},
          'Spectro': {'tip': 'Spectrum central wavelength', 'get_set': 'both'},
          'Slit': {'tip': 'Slit opening  in µm', 'get_set': 'both'},
          'Hole': {'tip': 'Confocal hole diamater in µm', 'get_set': 'both'},
          'Laser': {'tip': 'Selected laser in µm', 'get_set': 'both'},
          'Grating': {'tip': 'Selected Grating in grooves/mm', 'get_set': 'both'},
          'LaserPol': {'tip': 'Xplora laser polarization', 'get_set': 'both'},
          'RamanPol': {'tip': 'Xplora Raman Polarization', 'get_set': 'both'},
          'Pol1': {'tip': 'HR laser Polarization in deg', 'get_set': 'both'},
          'Pol2': {'tip': 'HR Raman Polarization in deg', 'get_set': 'both'},
          'Detector': {'tip': 'Selected Detector', 'get_set': 'get'},
          }


class Labspec6Client:

    def __init__(self):
        super().__init__()
        self.socket = None  #TCP socket to open in order to communicate with Labspec Server
        self.commandID = -1 #a unique identifier to match sent command and received answer from server
        self.lasers = []
        self.gratings = []
        self._exposure = 1
        self._accumulations = 1

    @property
    def timeout(self):
        if self.socket is not None:
            return self.socket.timeout
    @timeout.setter
    def timeout(self, timeout):
        if self.socket is not None:
            self.socket.settimeout(timeout)

    def prepare_one_acquisition(self):
        point_list = b'0 0'
        ret, data, extra = self.send_command('SetPointList', 1, 3, point_list)
        if ret == 'OK':
            ret, data, extra = self.send_command('EnableSpectralResponse')
            if ret == 'OK':
                self.wavelength_axis = data
                ret, data, extra = self.send_command('SetActivePoint', 0)
                if ret == 'OK':
                    return 'ready'
    @property
    def wavelength(self):
        ret, data, extra = self.send_command('GetRamanParam', 'Spectro')
        if ret == 'OK':
            return data

    @wavelength.setter
    def wavelength(self, value):
        ret, data, extra = self.send_command('SetRamanParameter', 'Spectro', value)
        if ret != 'OK':
            raise IOError('Wrong return from Server')


    @property
    def exposure(self):
       return self._exposure

    @exposure.setter
    def exposure(self, value):
        ret, data, extra = self.send_command('SetRamanParameter', 'Exposure', value)
        if ret != 'OK':
            raise IOError('Wrong return from Server')
        else:
            self._exposure = value

    @property
    def accumulations(self):
        return self._accumulations

    @accumulations.setter
    def accumulations(self, value):
        ret, data, extra = self.send_command('SetRamanParameter', 'Accumulations', value)
        if ret != 'OK':
            raise IOError('Wrong return from Server')
        else:
            self._accumulations = value

    @property
    def binning(self):
        ret, data, extra = self.send_command('GetRamanParam', 'Binning')
        if ret == 'OK':
            return int(data)

    @binning.setter
    def binning(self, value):
        """
        issue with the server, it says it doesnt recognise the binning command but set its value nevertheless
        """
        ret, data, extra = self.send_command('SetRamanParameter', 'Binning', int(value))
        # if ret != 'OK':
        #         #     raise IOError('Wrong return from Server')
        if self.binning != value:
            raise IOError('Wrong return from Server')


    @property
    def slit(self):
        ret, data, extra = self.send_command('GetRamanParam', 'Slit')
        if ret == 'OK':
            return data

    @slit.setter
    def slit(self, value):
        ret, data, extra = self.send_command('SetRamanParameter', 'Slit', value)
        if ret != 'OK':
            raise IOError('Wrong return from Server')

    @property
    def hole(self):
        ret, data, extra = self.send_command('GetRamanParam', 'Hole')
        if ret == 'OK':
            return data

    @hole.setter
    def hole(self, value):
        ret, data, extra = self.send_command('SetRamanParameter', 'Hole', value)
        if ret != 'OK':
            raise IOError('Wrong return from Server')

    @property
    def laser(self):
        ret, data, extra = self.send_command('GetRamanParam', 'Laser')
        if ret == 'OK':
            ind_laser, lasers = self.get_lasers()
            return lasers[ind_laser]

    @laser.setter
    def laser(self, value):
        ind_laser, lasers = self.get_lasers()
        ind_laser = lasers.index(value)
        ret, data, extra = self.send_command('SetRamanParameter', 'Laser', ind_laser)
        if ret != 'OK':
            raise IOError('Wrong return from Server')


    def get_lasers(self):
        ret, data, extra = self.send_command('GetRamanParam', 'Laser')
        if ret == 'OK':
            self.lasers = extra
            return int(data), extra

    def get_laser_wl(self):
        ret, data, extra = self.send_command('GetRamanParam', 'LaserWavelength')
        if ret == 'OK':
            return data

    @property
    def grating(self):
        ret, data, extra = self.send_command('GetRamanParam', 'Grating')
        if ret == 'OK':
            ind_grating, gratings = self.get_gratings()
            return gratings[ind_grating]

    @grating.setter
    def grating(self, value):
        ind_grating, gratings = self.get_gratings()
        ind_grating = gratings.index(value)
        ret, data, extra = self.send_command('SetRamanParameter', 'Grating', ind_grating)
        if ret != 'OK':
            raise IOError('Wrong return from Server')


    def get_gratings(self):
        ret, data, extra = self.send_command('GetRamanParam', 'Grating')
        if ret == 'OK':
            self.gratings = extra
            return int(data), extra

    def grab_spectrum(self):
        ret, data, extra = self.send_command('StartRamanMeasurement', 0)
        if ret == 'OK':
            return data

    def get_x_axis(self):
        ret, data, extra = self.send_command('EnableSpectralResponse')
        self.wavelength_axis = data
        return data

    def connect(self, IP='localhost', port=1234):
        # create an INET, STREAMing socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # now connect to the web server on port 80 - the normal http port
        self.socket.connect((IP, port))
        self.socket.settimeout(20) #set Timeout to 10s (by default) but should later be optimised given the exposure and accumulation number
        command_id, ret, data, extra = self.receive_data()
        if ret == 'OK':
            self.init_mandatory_settings()
        return ret, data, extra

    def init_mandatory_settings(self):
        self.exposure = self._exposure
        self.accumulations = self._accumulations

    def close(self):
        ret, data, extra = self.send_command('Logout')
        if ret == 'OK':
            self.socket.close()
            self.socket = None

    def receive_data(self, dtype='str'):
        data = b''
        extra = None
        while True:
            data += self.socket.recv(4096)

            if b'\r\n' in data:
                break
        data = data[:-2].decode().split(' ')
        command_id = data[0]
        ret = data[1]
        data_tmp = data[2:]
        if ret == 'OK':
            try:
                if dtype == 'str':
                    data = ' '.join(data_tmp)

                elif dtype == 'array':

                    data = np.array([float(d) for d in data_tmp[1:]])
                    if len(data) != int(data_tmp[0]):
                        raise IOError('Incorrect returned array length')

            except:
                data = ' '.join(data_tmp)

        elif dtype == 'param':
            if ret != 'Unknown':
                if ret != 'OK':
                    try:
                        data = float(ret)
                        ret = 'OK'
                    except ValueError: #could not convert ret to float because it is a string
                        ret += ' '.join(data_tmp)
                        data = None
                    if len(data_tmp) > 0:
                        data_tmp = ' '.join(data_tmp)
                        if '#' in data_tmp:
                            extra = data_tmp.split('#')
                            while '' in extra:
                                extra.pop(extra.index(''))

                else:
                    data = None
            else:
                data = ' '.join(data)

        else:
            data = ' '.join(data)

        try:
            command_id = int(command_id)
        except:
            pass

        return command_id, ret, data, extra

    def send_command(self, command, *args):
        self.commandID += 1
        if command == 'SetPointList':
            pointlist = args[-1]
            args = args[:-1]

        comm = f'{self.commandID} {command}'
        for arg in args:
            comm += f' {arg}'
        self.socket.send(comm.encode())
        if command == 'SetPointList':
            ret = self.socket.recv(4096)
            if b'OK Ready to receive' in ret:
                self.socket.send(pointlist)

        if COMMANDS[command] == 'array':
            command_id, ret, data, extra = self.receive_data('array')
        elif COMMANDS[command] == 'param':
            command_id, ret, data, extra = self.receive_data('param')
        else:
            command_id, ret, data, extra = self.receive_data()

        if command_id != self.commandID:
            raise IOError('The command ID returned from the Labspec server is incorrect')

        return ret, data, extra


