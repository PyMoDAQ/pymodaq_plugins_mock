import socket
import numpy as np

COMMANDS = {'GetRamanParam': 'param',
            'SetRamanParameter': 'param',
            'EnableSpectralResponse': 'array',
            'SetPointList': 'str',
            'SetActivePoint': 'array',
            'StartRamanMeasurement': 'array',
            'SetRamanParams': 'array',
            'Logout': 'str'
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
    """
    Wrapper around the Horiba RAMAN-AFM systems reversed interconnection protocol for LabSpec 6 Version 0.6.2
    Deals with internal TCP/IP communication, sending commands and interpreting returns
    Issue: The protocol in version 0.6.2 doesn't update the exposure time in Labspec GUI but still take it into account.
    Issue: Binning: issue with the server, it says it doesnt recognise the binning command but set its value nevertheless
    Issuie: exposure an accumulation cannot be read from labspec, they have to be set at initialization
    """

    def __init__(self):
        super().__init__()
        self._socket = None  #TCP socket to open in order to communicate with Labspec Server
        self._commandID = -1 #a unique identifier to match sent command and received answer from server
        self.lasers = [] #list of available lasers in the spectrometer
        self.gratings = [] #list of available gratings in the spectrometer
        self._exposure = 1 #exposure can be set but not retireved from labspec so it is stored here
        self._accumulations = 1 #accumulations can be set but not retireved from labspec so it is stored here

        self._timeout_mult = 5


    @property
    def timeout_mult(self):
        return self._timeout_mult

    @timeout_mult.setter
    def timeout_mult(self, timeout_mult):
        """set timeout multiplication factor value
        See Also:
        ---------
        self.prepare_N_acquisitions
        """
        self._timeout_mult = timeout_mult

    @property
    def timeout(self):
        """get timeout value of the tcp/ip communication
        """
        if self._socket is not None:
            return self._socket.timeout

    @timeout.setter
    def timeout(self, timeout):
        """set timeout value of the tcp/ip communication
        """
        if self._socket is not None:
            self._socket.settimeout(timeout)

    def prepare_N_acquisition(self, Npts=2):
        """
        Prepare acquisition before a grab. Normally it is used to prepare a map of Npoints. This is the AFM protocol way
        of doing things. However here, the map is set by default to 2 points, but acqusition is done on the first active
        point such that there is no time lag between successive acquisition. The mapping within labspec6 is however
        wrong, but pymodaq daq_scan is working properly like this.
        Parameters
        ----------
        Npts (int): the number of points to send to prepare the map
        """

        point_list = [b'0 0' for ind in range(Npts)] #fake list of points all equal to x=0, y=0
        Nbytes = Npts*3

        #get the approximate acquisition time to set the communication timeout
        ret, data, extra = self.send_command('GetRamanParam', 'AcquisitionTime')
        self.timeout = self._timeout_mult * data

        # send the list of points
        ret, data, extra = self.send_command('SetPointList', Npts, Nbytes, point_list)
        if ret == 'OK':
            ret, data, extra = self.send_command('EnableSpectralResponse')
            if ret == 'OK':
                self.wavelength_axis = data
                ret, data, extra = self.send_command('SetActivePoint', 0)
                if ret == 'OK':
                    return 'ready'

    @property
    def wavelength(self):
        """
        get the spectrometer central wavelength
        Returns
        -------
        float: central wavelength in nanometer
        """
        ret, data, extra = self.send_command('GetRamanParam', 'Spectro')
        if ret == 'OK':
            return data

    @wavelength.setter
    def wavelength(self, value):
        """
        set the spectrometer central wavelength
        Parameters
        ----------
        value (float): the central wavelength to set
        """
        ret, data, extra = self.send_command('SetRamanParameter', 'Spectro', value)
        if ret != 'OK':
            raise IOError('Wrong return from Server')


    @property
    def exposure(self):
        """
        get the exposure time in seconds
        """
        return self._exposure

    @exposure.setter
    def exposure(self, value):
        """
        set the exposure time in seconds
        """
        ret, data, extra = self.send_command('SetRamanParameter', 'Exposure', value)
        if ret != 'OK':
            raise IOError('Wrong return from Server')
        else:
            self._exposure = value

    @property
    def accumulations(self):
        """
        get the number of accumulations
        """
        return self._accumulations

    @accumulations.setter
    def accumulations(self, value):
        """
        set the number of accumulations
        """
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
        """
        get the slit size in microns (if available)
        """
        ret, data, extra = self.send_command('GetRamanParam', 'Slit')
        if ret == 'OK':
            return data

    @slit.setter
    def slit(self, value):
        """
        set the slit size in microns (if available)
        """
        ret, data, extra = self.send_command('SetRamanParameter', 'Slit', value)
        if ret != 'OK':
            raise IOError('Wrong return from Server')

    @property
    def hole(self):
        """
        get the confocal pinhole size in microns (if available)
        """
        ret, data, extra = self.send_command('GetRamanParam', 'Hole')
        if ret == 'OK':
            return data

    @hole.setter
    def hole(self, value):
        """
        set the confocal pinhole size in microns (if available)
        """
        ret, data, extra = self.send_command('SetRamanParameter', 'Hole', value)
        if ret != 'OK':
            raise IOError('Wrong return from Server')

    @property
    def laser(self):
        """
        get the current laser set in the spectrometer (as a string)
        """
        ret, data, extra = self.send_command('GetRamanParam', 'Laser')
        if ret == 'OK':
            ind_laser, lasers = self.get_lasers()
            return lasers[ind_laser]

    @laser.setter
    def laser(self, value):
        """
        set the current laser set in the spectrometer (as a string)
        strings identifiers obtained from self.get_lasers()
        """
        ind_laser, lasers = self.get_lasers()
        ind_laser = lasers.index(value)
        ret, data, extra = self.send_command('SetRamanParameter', 'Laser', ind_laser)
        if ret != 'OK':
            raise IOError('Wrong return from Server')


    def get_lasers(self):
        """
        get the list of configured lasers (as strings) and the index of the currently set
        Returns
        -------
        int: the laser index in the list of available lasers
        list: list of available lasers as string
        """
        ret, data, extra = self.send_command('GetRamanParam', 'Laser')
        if ret == 'OK':
            self.lasers = extra
            return int(data), extra

    def get_laser_wl(self):
        """
        get the current laser emission wavelength
        """
        ret, data, extra = self.send_command('GetRamanParam', 'LaserWavelength')
        if ret == 'OK':
            return data

    @property
    def grating(self):
        """
        get the the current grating set as a string identifier
        """
        ret, data, extra = self.send_command('GetRamanParam', 'Grating')
        if ret == 'OK':
            ind_grating, gratings = self.get_gratings()
            return gratings[ind_grating]

    @grating.setter
    def grating(self, value):
        """
        set the the current grating using its string identifier
        See Also
        --------
        self.get_gratings
        """
        ind_grating, gratings = self.get_gratings()
        ind_grating = gratings.index(value)
        ret, data, extra = self.send_command('SetRamanParameter', 'Grating', ind_grating)
        if ret != 'OK':
            raise IOError('Wrong return from Server')


    def get_gratings(self):
        """
        get the list as string identifiers of the configured gratings
        Returns
        -------
        int: the grating index in the list of available gratings
        list: list of available gratings as string
        """
        ret, data, extra = self.send_command('GetRamanParam', 'Grating')
        if ret == 'OK':
            self.gratings = extra
            return int(data), extra

    def grab_spectrum(self):
        """
        Grab a spectrum with current configuration
        Returns
        -------
        array: numpy array with the spectral intensity
        """
        ret, data, extra = self.send_command('StartRamanMeasurement', 0)
        if ret == 'OK':
            return data

    def get_x_axis(self):
        """
        Get the wavelength calibration for each pixels
        Returns
        -------
        array: numpy array with the pixels wavelength (in nanometer)
        """
        ret, data, extra = self.send_command('EnableSpectralResponse')
        self.wavelength_axis = data
        return data

    def connect(self, IP='localhost', port=1234):
        """
        enable the TCP/IP connection
        Parameters
        ----------
        IP (str): string identifier of the server 'localhost' or IP identifier
        port (int): communication port, default 1234

        Returns
        -------
        str: success or not of the initialization
        str: identifiant of the protocol
        None
        """
        # create an INET, STREAMing socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # now connect to the web server on port 80 - the normal http port
        self._socket.connect((IP, port))
        self.timeout = 20 #set Timeout to 20s (by default) but should later be optimised given the exposure and accumulation number
        command_id, ret, data, extra = self.receive_data()
        if ret == 'OK':
            self.init_mandatory_settings()
        return ret, data, extra

    def init_mandatory_settings(self):
        """
        set the exposure and accumulations as those cannot be read from labspec
        """
        self.exposure = self._exposure
        self.accumulations = self._accumulations

    def close(self):
        """
        Send a Logout command to the labspec server and close the socket connection
        """
        ret, data, extra = self.send_command('Logout')
        if ret == 'OK':
            self._socket.close()
            self._socket = None

    def receive_data(self, dtype='str'):
        """
        Receive and interpret data from the tcp/ip connection
        Parameters
        ----------
        dtype (str): aither 'str' or 'param' or 'array'

        Returns
        -------
        command_id: (int) command identifier
        ret: (str) success or error of the communication
        data: type depends on the dtype argument, could be a string, number or array
        extra: extra info (for instance list of lasers or gratings...)
        See Also
        --------
        self.get_lasers, self.get_gratings
        """
        data = b''
        extra = None
        while True:
            data += self._socket.recv(4096)

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
        """
        send an interpreted command following the AFM Labspec protocol
        Parameters
        ----------
        command (str): any of the COMMANDS dictionary keys defined above
        args: arguments to be added to the command by string concatenation

        Returns
        -------
        ret: (str) success or error of the communication
        data: type depends on the command argument, could be a string, number or array
        extra: extra info usually None
        """
        self._commandID += 1
        comm = f'{self._commandID} {command}'

        if command == 'SetPointList':
            pointlist = args[-1]
            args = args[:-1]

        for arg in args:
            comm += f' {arg}'
        self._socket.send(comm.encode())

        if command == 'SetPointList':
            ret = self._socket.recv(4096)
            if b'OK Ready to receive' not in ret:
                raise IOError(f'The command {comm} returned with an error: {ret}')
            for ind, point in enumerate(pointlist):
                self._socket.send(point)
                if ind < len(pointlist)-1:
                    ret = self._socket.recv(4096)
                    if b'OK Point' not in ret:
                        raise IOError(f'Issue with the list of point, ind:{ind}')

        command_id, ret, data, extra = self.receive_data(COMMANDS[command])

        if command_id != self._commandID:
            raise IOError('The command ID returned from the Labspec server is incorrect')

        return ret, data, extra


