import PyDAQmx
import ctypes
from enum import IntEnum


class DAQ_NIDAQ_source(IntEnum):
    """
        Enum class of NIDAQ_source

        =============== ==========
        **Attributes**   **Type**
        *Analog_Input*   int
        *Counter*        int
        =============== ==========
    """
    Analog_Input = 0
    Counter = 1
    Analog_Output = 2

    @classmethod
    def names(cls):
        return [name for name, member in cls.__members__.items()]

class DAQ_analog_types(IntEnum):
    """
        Enum class of Ai types

        =============== ==========
        **Attributes**   **Type**
        =============== ==========
    """
    Voltage = PyDAQmx.DAQmx_Val_Voltage
    Current = PyDAQmx.DAQmx_Val_Current
    Thermocouple = PyDAQmx.DAQmx_Val_Temp_TC

    @classmethod
    def names(cls):
        return [name for name, member in cls.__members__.items()]

    @classmethod
    def values(cls):
        return [cls[name].value for name, member in cls.__members__.items()]

class DAQ_thermocouples(IntEnum):
    """
        Enum class of thermocouples type

        =============== ==========
        **Attributes**   **Type**
        =============== ==========
    """
    J = PyDAQmx.DAQmx_Val_J_Type_TC
    K = PyDAQmx.DAQmx_Val_K_Type_TC
    N = PyDAQmx.DAQmx_Val_N_Type_TC
    R = PyDAQmx.DAQmx_Val_R_Type_TC
    S = PyDAQmx.DAQmx_Val_S_Type_TC
    T = PyDAQmx.DAQmx_Val_T_Type_TC
    B = PyDAQmx.DAQmx_Val_B_Type_TC
    E = PyDAQmx.DAQmx_Val_E_Type_TC

    @classmethod
    def names(cls):
        return [name for name, member in cls.__members__.items()]

class DAQ_termination(IntEnum):
    """
        Enum class of thermocouples type

        =============== ==========
        **Attributes**   **Type**
        =============== ==========
    """
    Auto = PyDAQmx.DAQmx_Val_Cfg_Default
    RSE = PyDAQmx.DAQmx_Val_RSE
    NRSE = PyDAQmx.DAQmx_Val_NRSE
    Diff = PyDAQmx.DAQmx_Val_Diff
    Pseudodiff = PyDAQmx.DAQmx_Val_PseudoDiff

    @classmethod
    def names(cls):
        return [name for name, member in cls.__members__.items()]

class Edge(IntEnum):
    """
    """
    Rising = PyDAQmx.DAQmx_Val_Rising
    Falling = PyDAQmx.DAQmx_Val_Falling

    @classmethod
    def names(cls):
        return [name for name, member in cls.__members__.items()]


class ClockSettings:
    def __init__(self, frequency=1000, Nsamples=100, edge=Edge.names()[0], ):
        assert edge in Edge.names()
        self.frequency = frequency
        self.Nsamples = Nsamples
        self.edge = edge
        self.mode = PyDAQmx.DAQmx_Val_FiniteSamps


class Channel:
    def __init__(self, name='', source=DAQ_NIDAQ_source.names()[0]):
        """
        Parameters
        ----------

        """
        self.name = name
        assert source in DAQ_NIDAQ_source.names()
        self.source = source


class AChannel(Channel):
    def __init__(self, analog_type=DAQ_analog_types.names()[0], value_min=-10., value_max=+10., **kwargs):
        """
        Parameters
        ----------
        min: (float) minimum value for the configured input channel (could be voltage, amps, temperature...)
        max: (float) maximum value for the configured input channel
        """
        super().__init__(**kwargs)
        self.value_min = value_min
        self.value_max = value_max
        self.analog_type = analog_type

class AIChannel(AChannel):
    def __init__(self, termination = DAQ_termination.names()[0], **kwargs):
        super().__init__(**kwargs)
        assert termination in DAQ_termination.names()
        self.termination = termination

class AIThermoChannel(AIChannel):
    def __init__(self, thermo_type=DAQ_thermocouples.names()[0], **kwargs):
        super().__init__(**kwargs)
        assert thermo_type in DAQ_thermocouples.names()
        self.thermo_type = thermo_type

class AOChannel(AChannel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Counter(Channel):
    def __init__(self, edge=Edge.names()[0], **kwargs):
        assert edge in Edge.names()
        super().__init__(**kwargs)
        self.edge = edge

class NiDAQmx:

    def __init__(self):
        super().__init__()
        self.devices = []
        self.channels = []
        self._selected_channels = []
        self._device = None
        self._task = None
        self.update_NIDAQ_devices()
        self.update_NIDAQ_channels()


    @property
    def selected_channels(self):
        return self._selected_channels

    @selected_channels.setter
    def selected_channels(self, selected_channels):
        """

        Parameters
        ----------
        selected_channels: list of Channel Object or inherited ones

        """
        assert(isinstance(selected_channels, list))
        for sel in selected_channels:
            assert(isinstance(sel, Channel))
            if sel['ch_name'] not in self.channels:
                raise IOError(f'your selected channel: {str(sel)} is not known or connected')
        self._selected_channels = selected_channels

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, device):
        if device not in self.devices:
            raise IOError(f'your device: {device} is not known or connected')
        self._device = device

    def update_NIDAQ_devices(self):
        self.devices = self.get_NIDAQ_devices()

    @classmethod
    def get_NIDAQ_devices(cls):
        """Get list of NI connected devices

        Returns
        -------
        list
            list of devices as strings to be used in subsequent commands
        """
        try:
            buff = PyDAQmx.create_string_buffer(128)
            PyDAQmx.DAQmxGetSysDevNames(buff, len(buff))
            devices = buff.value.decode().split(',')
            return devices
        except:
            return []

    def update_NIDAQ_channels(self, source_type=None):
        self.channels = self.get_NIDAQ_channels(self.devices, source_type=source_type)

    @classmethod
    def get_NIDAQ_channels(cls, devices=None, source_type=None):
        """Get the list of available channels for all NiDAq connected devices

        Parameters
        ----------
        devices: list
                 list of strings, each one being a connected device
        source_type: str
                     One of the entries of DAQ_NIDAQ_source enum

        Returns
        -------
        List of str containing device and channel names

        """
        if devices is None:
            devices = cls.get_NIDAQ_devices()

        if source_type is None:
            source_type = DAQ_NIDAQ_source.names()
        if not isinstance(source_type, list):
            source_type = [source_type]
        channels_tot = []
        if not not devices:
            for device in devices:
                for source in source_type:
                    buff = PyDAQmx.create_string_buffer(1024)
                    if source == DAQ_NIDAQ_source['Analog_Input'].name:  # analog input
                        PyDAQmx.DAQmxGetDevAIPhysicalChans(device, buff, len(buff))

                    elif source == DAQ_NIDAQ_source['Counter'].name:  # counter
                        PyDAQmx.DAQmxGetDevCIPhysicalChans(device, buff, len(buff))

                    elif source == DAQ_NIDAQ_source['Analog_Output'].name:  # analog output
                        PyDAQmx.DAQmxGetDevAOPhysicalChans(device, buff, len(buff))

                    channels = buff.value.decode()[:].split(',')
                    if channels != ['']:
                        channels_tot.extend(channels)

        return channels_tot

    def update_task(self, channels=[AIChannel()], clock_settings=ClockSettings()):
        """

        """

        try:
            if self._task is not None:
                if isinstance(self._task, PyDAQmx.Task):
                    self._task.ClearTask()
                else:
                    self._task = None

            self._task = PyDAQmx.Task()

            for channel in channels:

                if channel.source == 'Analog_Input': #analog input
                    if channel.analog_type == "Voltage":
                        err_code = self._task.CreateAIVoltageChan(channel.name, "",
                                     DAQ_termination[channel.termination].value,
                                     channel.value_min,
                                     channel.value_max,
                                     PyDAQmx.DAQmx_Val_Volts, None)

                    elif channel.analog_type == "Current":
                        err_code = self._task.CreateAICurrentChan(channel.name, "",
                                                                  DAQ_termination[channel.termination].value,
                                                                  channel.value_min,
                                                                  channel.value_max,
                                                                  PyDAQmx.DAQmx_Val_Amps, PyDAQmx.DAQmx_Val_Internal,
                                                                  0., None)

                    elif channel.analog_type == "Thermocouple":
                        err_code = self._task.CreateAIThrmcplChan(channel.name, "",
                                                                  channel.value_min,
                                                                  channel.value_max,
                                                                  PyDAQmx.DAQmx_Val_DegC,
                                                                  DAQ_termination[channel.thermo_type].value,
                                                                  PyDAQmx.DAQmx_Val_BuiltIn, 0., "")

                    if err_code is None:
                        err_code = self._task.CfgSampClkTiming(None,
                                                               clock_settings.frequency,
                                                               Edge[clock_settings.edge].value,
                                                               PyDAQmx.DAQmx_Val_FiniteSamps,
                                                               clock_settings.Nsamples)

                        if err_code is not None:
                            status = self._task.GetErrorString(err_code)
                            raise IOError(status)
                    else:
                        status = self._task.GetErrorString(err_code)
                        raise IOError(status)

                elif channel.source == 'Counter': #counter
                    err_code = self._task.CreateCICountEdgesChan(channel.name, "",
                                                               Edge[channel.edge].value, 0,
                                                               PyDAQmx.DAQmx_Val_CountUp)
                    if err_code is not None:
                        status = self._task.GetErrorString(err_code)
                        raise IOError(status)

            self.status.initialized = True
            self.status.controller = self._task
        except Exception as e:
            print(e)

    def close(self):
        if self._task is not None:
            self._task.ClearTask()

if __name__ == '__main__':
    print(NiDAQmx.get_NIDAQ_channels())
    pass