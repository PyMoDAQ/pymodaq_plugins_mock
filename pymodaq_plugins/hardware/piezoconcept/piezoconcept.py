import pyvisa
import numpy as np

class Position(object):
    units=['n', 'u']
    axes=['X', 'Y']

    def __init__(self,axis='X', pos=100., unit='u'):
        if axis in self.axes:
            self.axis = axis
        else:
            raise Exception('{:s} is not a valid axis'.format(axis))
        self.pos = pos
        if unit in self.units:
            self.unit = unit
        else:
            raise Exception('{:s} is not a valid unit'.format(unit))
        
    def __str__(self):
        return 'Axis {:s} at position {:f}{:s}'.format(self.axis, self.pos, self.unit)    
    
    def __repr__(self):
        return self.__str__()
    
class Time(object):
    units=['u', 'm', 's'] #valid units
    def __init__(self,time=100., unit='u'):
        self.time = time
        if unit in self.units:
            self.unit = unit
        else:
            raise Exception('{:s} is not a valid unit'.format(unit))
            
    def __str__(self):
        return 'Time: {:f}{:s}'.format(self.time, self.unit)    
    
    def __repr__(self):
        return self.__str__()  
    
class PiezoConcept(object):

    def __init__(self):
        super().__init__()
        self._piezo=None
        self._VISA_rm = pyvisa.ResourceManager()
        self.com_ports = self.get_ressources()

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, to):
        self._timeout = to
        self._piezo.timeout = to

    def get_ressources(self):
        infos=self._VISA_rm.list_resources_info()
        com_ports=[infos[key].alias for key in infos.keys()]
        return com_ports
    
    def init_communication(self, com_port):
        if com_port in self.com_ports:
            self._piezo = self._VISA_rm.open_resource(com_port)
            # set attributes
            self._piezo.baud_rate = 115200
            self._piezo.data_bits = 8
            self._piezo.stop_bits = pyvisa.constants.StopBits['one']
            self._piezo.parity = pyvisa.constants.Parity['none']
            self._piezo.flow_control = 0
            self._piezo.read_termination = self._piezo.LF
            self._piezo.write_termination = self._piezo.LF
            self.timeout = 2000
        else:
            raise IOError('{:s} is not a valid port'.format(com_port))
            
    def close_communication(self):
        self._piezo.close()
        self._VISA_rm.close() 
        
    def get_controller_infos(self):
        self._write_command('INFOS')
        return self._get_read()

    def _query(self, command):
        ret = self._piezo.query(command)
        return ret

    def _write_command(self, command):
        self._piezo.write(command)

    
    def _get_read(self):
        self._piezo.timeout = 50
        info = ''
        try:
            while True:
                info += self._piezo.read(encoding='mbcs')+'\n'
        except pyvisa.errors.VisaIOError as e:
            pass
        self._piezo.timeout = self._timeout
        return info
    
    def move_axis(self, move_type='ABS', pos=Position(axis='X', pos=100, unit='n')):
        cmd = '{:s} {:d}{:s}'.format(pos.axis, int(pos.pos), pos.unit)
        if move_type == 'ABS':
            cmd = 'MOVE' + cmd

        elif move_type == 'REL':
            cmd = 'MOVR' + cmd
        else:
            raise Exception('{:s} is not a valid displacement type'.format(move_type))

        ret = self._query(cmd)
        return ret

    def get_position(self, axis='X'):
        """ return the given axis position always in nm
        Parameters
        ----------
        axis: str, default 'X'
            either 'X' or 'Y'
        Returns
        -------
        pos
            an instance of the Position class containing the attributes:
                axis (either ('X' or 'Y'), pos and unit (either 'u' or 'n')
        """    
        pos_str = self._query('GET_{:s}'.format(axis))
        pos_list = pos_str.split(' ')
        unit = pos_list[1][0]
        if unit == 'u':
            pos = int(float(pos_list[0])*1000)
            unit = 'n'
        else:
            pos = int(pos_list[0])

        pos = Position(axis, pos, unit)
        return pos

    def set_time_interval(self, time=Time(50., 'm')):
        if isinstance(time, Time):
            self._query('STIME {:.0f}{:s}'.format(time.time, time.unit))
        else:
            raise Exception('Wrong time argument')
            
    def get_time_interval(self):
        time_str = self._piezo.query('GTIME')
        time_list = time_str.split(' ')
        return Time(float(time_list[0]), time_list[1][0])
    
    def set_positions_simple(self, Xpositions=[], Ypositions=[], Zpositions=[]):
        """ prepare the controller with arbitrary positions in nanometers
        Parameters
        ----------
        Xpositions: (ndarray, dtype=int) X positions in nm
        Ypositions: (ndarray, dtype=int) X positions in nm
        Zpositions: (ndarray, dtype=int) X positions in nm
        """
        Nx = len(Xpositions)
        Ny = len(Ypositions)
        Nz = len(Zpositions)
        
        ret = self._query('ARBWF {:d} {:d} {:d}'.format(Nx, Ny, Nz))
        if ret != 'Ok':
            raise IOError('{:}: Positions not set'.format(ret))
        for xpos in Xpositions:
            ret = self._query('ADDPX {:d}{:s}'.format(int(xpos), 'n'))
            if ret != 'Ok':
                raise IOError('{:}: Added point not set'.format(ret))

        for ypos in Ypositions:
            ret = self._query('ADDPY {:d}{:s}'.format(int(ypos), 'n'))
            if ret != 'Ok':
                raise IOError('{:}: Added point not set'.format(ret))

        for zpos in Zpositions:
            ret = self._query('ADDPZ {:d}{:s}'.format(int(zpos), 'n'))
            if ret != 'Ok':
                raise IOError('{:}: Added point not set'.format(ret))

    def run_simple(self):
        """ run the previously set waveforms
        After writing the command the controller should return the number of steps for each axis, for instance:
        '21.00\n11.00\n2.00\n'
        then :
        'Scan completed\n' once the scan is completed
        check this return using self._get_read(), in order to check when the scan is finished

        """
        self._write_command('RUNWF')


    def set_positions_arbitrary(self, positions):
        """ prepare the controller with arbitrary positions. At least one array should be set
        Parameters
        ----------
        positions: (list) of 2 (or 3 if Z) arbitrary positions
        """

        Npoints = len(positions)
        self._get_read()
        ret = self._query('ARB3D {:d}'.format(Npoints))
        if ret != 'Ok':
            raise IOError('{:}: ARB3D not set'.format(ret))
        
        for pos in positions:
            if len(pos) == 2:
                pos.append(0)
            pos = [int(p) for p in pos]
            ret = self._query('ADD3D {:d}n {:d}n {:d}n'.format(*pos))
            if ret != 'Ok':
                raise IOError('{:}: ADD3D not set'.format(ret))
            
    def run_arbitrary(self):
        self._write_command('RUN3D')
        
    def get_TTL_state(self, port=1):
        """
        Return the configuration state of the given TTL (1 to 4)
        Parameters
        ----------
        port: (int) TTL number (1 to 4)

        Returns
        -------
        list of str : on the form 'status:\nInput rising\nAxis1\n'
        """
        if port > 4 or port < 1:
            raise Exception('Invalid IO port number (1-4)')
        else:
            self._piezo.write('DISIO {:d}'.format(port))
            info = self._get_read()
            info = info.split('\n')
        return info
    
    def set_TTL_state(self, port, axis, IO='disabled', ttl_options=dict(slope='rising', type='start', ind_start=0, ind_stop=0)):
        """ define a given TTL input/output
        Parameters
        ----------
        port: int between 1 and 4
        axis: str either ('X', 'Y' or 'Z')
        IO: str
            either 'disabled', 'input' or 'output'
        ttl_options: dict
            containing the keys:
                slope: str either 'rising' or 'falling' (valid only in 'input' IO mode)
                type: str either 'start', 'end', 'given_step' or 'gate_step' (valid only in 'output' IO mode)
                ind_start: step number to start the TTL (valid for given_step and gate_step mode)
                ind_stop: step number to stop the gate (valid for gate_step mode)
        """
        axes = ['X', 'Y', 'Z']
        ind_axis = axes.index(axis) + 1
        if IO == 'disabled':
            ret = self._write_command('CHAIO {:d}{:s}'.format(port, IO[0]))
        elif IO == 'input':
            ret = self._write_command('CHAIO {:d}{:s}{:d}{:s}'.format(port, IO[0], ind_axis, ttl_options['slope'][0]))
        elif IO == 'output':
            if ttl_options['type'] == 'start':
                ret = self._write_command('CHAIO {:d}{:s}{:d}{:s}'.format(port, 'o', ind_axis, 's'))
            elif ttl_options['type'] == 'end':
                ret = self._write_command('CHAIO {:d}{:s}{:d}{:s}'.format(port, 'o', ind_axis, 'e'))
            elif ttl_options['type'] == 'given_step':
                ret = self._write_command('CHAIO {:d}{:s}{:d}{:s}{:d}'.format(port, 'o', ind_axis, 'n', ttl_options['ind_start']))
            elif ttl_options['type'] == 'gate_step':
                ret = self._write_command('CHAIO {:d}{:s}{:d}{:s}{:d}-{:d}'.format(port, 'o', ind_axis, 'g', ttl_options['ind_start'],
                                                             ttl_options['ind_stop']))

        else:
            raise Exception('Not valid IO type for TTL')

        info = self._get_read()
        info = info.split('\n')

        if info[-2] != 'Ok':
            raise IOError('{:}: set_TTL_state wrong return'.format(ret))

class PiezoConceptPI(PiezoConcept):
    def __init__(self):
        super().__init__()

    def get_controller_infos(self):
        self._write_command('*IDN?')
        return self._get_read()

    def get_position(self, axis='X'):
        """ return the given axis position always in nm
        Parameters
        ----------
        axis: str, default 'X'
            either 'X' or 'Y'
        Returns
        -------
        pos
            an instance of the Position class containing the attributes:
                axis (either ('X' or 'Y'), pos and unit (either 'u' or 'n')
        """
        ind = ['X', 'Y'].index(axis) + 1
        pos_str = self._query(f'POS? {ind}')
        pos = Position(axis, float(pos_str), 'u')
        return pos

    def move_axis(self, move_type='ABS', pos=Position(axis='X', pos=100., unit='u')):
        if pos.unit == 'n':
            pos.pos = pos.pos / 1000
            pos.unit = 'u'
        ind = ['X', 'Y'].index(pos.axis) + 1
        cmd = f'{ind} {pos.pos}'
        if move_type == 'ABS':
            cmd = 'MOV ' + cmd
        else:
            raise Exception('{:s} is not a valid displacement type'.format(move_type))

        ret = self._write_command(cmd)
        return ret