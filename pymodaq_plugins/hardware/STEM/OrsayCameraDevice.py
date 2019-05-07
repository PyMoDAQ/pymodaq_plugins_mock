# standard libraries
import copy
import ctypes
import gettext
import numpy
import threading
import typing
import time
from nion.swift.model import PlugInManager
import traceback

# third party libraries
from . import orsaycamera

# local libraries
from nion.data import Calibration
from nion.swift.model import HardwareSource
from nion.utils import Registry

from nion.instrumentation import camera_base

from enum import Enum

_ = gettext.gettext

# STEM_CONTROLLER_ID = "autostem_controller"

class Orsay_Data(Enum):
    s16 = 2
    s32 = 3
    uns16 = 6
    uns32 = 7
    float = 11
    real = 12

class CameraDevice(camera_base.Camera):

    def __init__(self, manufacturer, model, sn, simul):
        self.__config_dialog_handler = None
        self.camera = orsaycamera.orsayCamera(manufacturer, model, sn, simul)
        self.__sensor_dimensions = self.camera.getCCDSize()
        self.__readout_area = 0, 0, *self.__sensor_dimensions
        self.__orsay_binning = self.camera.getBinning()
        self.sizex, self.sizey = self.camera.getImageSize()
        self.sizez = 1
        self._last_time = time.time()

        # register data locker for focus acquisition
        self.fnlock = orsaycamera.DATALOCKFUNC(self.__data_locker)
        self.camera.registerDataLocker(self.fnlock)
        self.fnunlock = orsaycamera.DATAUNLOCKFUNC(self.__data_unlocker)
        self.camera.registerDataUnlocker(self.fnunlock)
        self.imagedata = None
        self.imagedata_ptr = None
        self.has_data_event = threading.Event()

        # register data locker for SPIM acquisition
        self.fnspimlock = orsaycamera.SPIMLOCKFUNC(self.__spim_data_locker)
        self.camera.registerSpimDataLocker(self.fnspimlock)
        self.fnspimunlock = orsaycamera.SPIMUNLOCKFUNC(self.__spim_data_unlocker)
        self.camera.registerSpimDataUnlocker(self.fnspimunlock)
        self.fnspectrumlock = orsaycamera.SPECTLOCKFUNC(self.__spectrum_data_locker)
        self.camera.registerSpectrumDataLocker(self.fnspectrumlock)
        self.fnspectrumunlock = orsaycamera.SPECTUNLOCKFUNC(self.__spectrum_data_unlocker)
        self.camera.registerSpectrumDataUnlocker(self.fnspectrumunlock)
        self.spimimagedata = None
        self.spimimagedata_ptr = None
        self.has_spim_data_event = threading.Event()

        bx, by = self.camera.getBinning()
        port = self.camera.getCurrentPort()
        d = {
            "exposure_ms": 10,
            "h_binning": bx,
            "v_binning": by,
            "acquisition_style": "2d",
            "acquisition_mode": "Focus",
            "spectra_count": 10,
            "multiplication": self.camera.getMultiplication()[0],
            "area": self.camera.getArea(),
            "port": port,
            "speed": self.camera.getCurrentSpeed(port),
            "gain": self.camera.getGain(port),
            "turbo_mode_enabled": self.camera.getTurboMode()[0],
            "video_threshold": self.camera.getVideoThreshold(),
            "processing": None
        }


        self.current_camera_settings = CameraFrameParameters(d)
        self.__hardware_settings = self.current_camera_settings

        self.camera.setExposureTime(self.current_camera_settings.exposure_ms / 1000)
        self.camera.setAccumulationNumber(self.current_camera_settings.spectra_count)
        self.__frame_number = 0

        self.__processing = None

        self.__acqon = False
        self.__acqspimon = False

        # self.__area = 0, 0, self.__readout_area[3], self.__readout_area[2]
        self.isKURO = model.find("KURO") >= 0
        self.isProEM = model.find("ProEM") >= 0
        self.__calibration_controls = {}
        if self.isProEM:
            self.__calibration_controls = {
                "x_scale_control": "ProEM_EELS_eVperpixel",
                "x_offset_control": "ProEM_EELS_eVOffset",
                "x_units_value": "eV",
                "y_scale_control": "ProEM_EELS_radsperpixel",
                "y_units_value": "rad",
                "intensity_units_value": "counts",
                "counts_per_electron_control": "ProEM_EELS_CountsPerElectron"
            }

        if self.isKURO:
            self.__calibration_controls = {
                "x_scale_control": "KURO_EELS_eVperpixel",
                "x_offset_control": "KURO_EELS_eVOffset",
                "x_units_value": "eV",
                "y_scale_control": "ProEM_EELS_radsperpixel",
                "y_units_value": "rad",
                "intensity_units_value": "counts",
                "counts_per_electron_control": "KURO_EELS_CountsPerElectron"
            }

        #print(self.__calibration_controls)

    def close(self):
        self.camera.stopSpim(True)
        #self.camera.close()

    def create_frame_parameters(self, d: dict) -> dict:
        return self.current_camera_settings

    def set_frame_parameters(self, frame_parameters : dict) -> None:
        acqon = self.__acqon
        if acqon:
            self.stop_live()

        if self.__hardware_settings.exposure_ms != frame_parameters.exposure_ms:
            self.__hardware_settings.exposure_ms = frame_parameters.exposure_ms
            self.camera.setExposureTime(frame_parameters.exposure_ms)

        if "acquisition_style" in frame_parameters:
            self.__hardware_settings.acquisition_style = frame_parameters.acquisition_style
            if self.__hardware_settings.acquisition_mode != frame_parameters.acquisition_mode:
                self.__hardware_settings.acquisition_mode = frame_parameters.acquisition_mode
            print(f"acquisition mode[camera]: {self.__hardware_settings.acquisition_mode}")
            self.__hardware_settings.spectra_count = frame_parameters.spectra_count

        if "port" in frame_parameters:
            if self.__hardware_settings.port != frame_parameters.port:
                self.__hardware_settings.port = frame_parameters.port
                self.camera.setCurrentPort(frame_parameters.port)

        if self.isKURO:
            frame_parameters.speed = 1

        if "speed" in frame_parameters:
            if self.__hardware_settings.speed != frame_parameters.speed:
                self.__hardware_settings.speed = frame_parameters.speed
                self.camera.setSpeed(self.__hardware_settings.port, frame_parameters.speed)

        if "area" in frame_parameters:
            if any(i != j for i,j in zip(self.__hardware_settings.area, frame_parameters.area)):
    # if change area, put back binning to 1,1 temporarily in order to avoid conflicts, binnig will then be setup later
                self.__hardware_settings.h_binning = 1
                self.__hardware_settings.v_binning = 1
                self.camera.setBinning(self.__hardware_settings.h_binning, self.__hardware_settings.v_binning)
                self.__hardware_settings.area = frame_parameters.area
                self.camera.setArea(self.__hardware_settings.area)

        if ("h_binning" in frame_parameters) and ("v_binning" in frame_parameters):
            if (self.__hardware_settings.h_binning != frame_parameters.h_binning)\
                    or (self.__hardware_settings.v_binning != frame_parameters.v_binning):
                self.camera.setBinning(frame_parameters.h_binning, frame_parameters.v_binning)
                self.__hardware_settings.h_binning, self.__hardware_settings.v_binning = self.camera.getBinning()

        if "gain" in frame_parameters:
            if self.__hardware_settings.gain != frame_parameters.gain:
                self.__hardware_settings.gain = frame_parameters.gain
                self.camera.setGain(self.__hardware_settings.gain)
        if "spectra_count" in frame_parameters:
            self.__hardware_settings.spectra_count = frame_parameters.spectra_count
            self.camera.setAccumulationNumber(self.__hardware_settings.spectra_count)
        if "video_threshold" in frame_parameters:
            self.__hardware_settings.video_threshold = frame_parameters.video_threshold
            self.camera.setVideoThreshold(self.__hardware_settings.video_threshold)

        if "processing" in frame_parameters:
            self.__hardware_settings.processing = frame_parameters.processing

        if acqon:
            self.start_live()

    # def _get_frame_parameters(self):
    #     # only used by the camera settings
    #     bx, by = self.camera.getBinning()
    #     port = self.camera.getCurrentPort()
    #     sensor_dimensions = self.camera.getCCDSize()
    #     d = {
    #         "exposure_ms": self.current_camera_settings.exposure_ms,
    #         "h_binning": bx,
    #         "v_binning": by,
    #         "acquisition_style": self.current_camera_settings.acquisition_style,
    #         "acquisition_mode": self.current_camera_settings.acquisition_mode,
    #         "spectra_count": self.camera.getAccumulateNumber(),
    #         "multiplication": self.camera.getMultiplication()[0],
    #         "area": self.camera.getArea(),
    #         "port": port,
    #         "speed": self.camera.getCurrentSpeed(port),
    #         "gain": self.camera.getGain(port),
    #         "turbo_mode_enabled": self.camera.getTurboMode()[0],
    #         "video_threshold": self.camera.getVideoThreshold(),
    #         "processing": self.current_camera_settings.processing
    #     }
    #     return CameraFrameParameters(d)
    #
    def __numpy_to_orsay_type(self, array: numpy.array):
        orsay_type = Orsay_Data.float
        if array.dtype == numpy.double:
            orsay_type = Orsay_Data.real
        if array.dtype == numpy.int16:
            orsay_type = Orsay_Data.s16
        if array.dtype == numpy.int32:
            orsay_type = Orsay_Data.s32
        if array.dtype == numpy.uint16:
            orsay_type = Orsay_Data.uns16
        if array.dtype == numpy.uint32:
            orsay_type = Orsay_Data.uns32
        return orsay_type.value

    def __data_locker(self, gene, data_type, sx, sy, sz):
        sx[0] = self.sizex
        sy[0] = self.sizey
        sz[0] = 1
        data_type[0] = self.__numpy_to_orsay_type(self.imagedata)
        return self.imagedata_ptr.value

    def __data_unlocker(self, gene, new_data):
        self.__frame_number += 1
        if new_data:
            t = time.time()
            if t - self._last_time > 0.1:
                self.has_data_event.set()
                self._last_time = t
        status = self.camera.getCCDStatus()
        if status["mode"] == "Cumul":
            self.__frame_number = status["accumulation_count"]
        if status["mode"] == "idle":
            hardware_source = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                self.camera_id)
            hardware_source.stop_playing()

    def __spim_data_locker(self, gene, data_type, sx, sy, sz):
        sx[0] = self.sizex
        sy[0] = self.sizey
        sz[0] = self.sizez
        #data_type >= 100 force spectrum data on first axis.
        data_type[0] = 100 + self.__numpy_to_orsay_type(self.spimimagedata)
        # if self.current_camera_settings.acquisition_mode != "2D-Chrono":
        #     data_type[0] = 100 + self.__numpy_to_orsay_type(self.spimimagedata)
        #print(f"spim lock {sx[0]} {sy[0]} {sz[0]}")
        return self.spimimagedata_ptr.value

    def __spim_data_unlocker(self, gene :int, new_data : bool, running : bool):
        status = self.camera.getCCDStatus()
        if status["mode"] == "Spectrum imaging":
            self.__frame_number = status["current spectrum"]
        if "Chrono" in status["mode"]:
            if new_data:
                self.has_data_event.set()
        else:
            if not running:
                # just stopped, send last data anyway.
                self.has_spim_data_event.set()
                print("spim done")
        if not running:
            hardware_source = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                self.camera_id)
            hardware_source.stop_playing()

    def __spectrum_data_locker(self, gene, data_type, sx) -> None:
        if self.__acqon and self.__acqspimon and (self.current_camera_settings.exposure_ms >= 10):
            sx[0] = self.sizex
            data_type[0] = self.__numpy_to_orsay_type(self.imagedata)
            return self.imagedata_ptr.value
        else:
            return None

    def __spectrum_data_unlocker(self, gene, newdata):
        if (self.current_camera_settings.acquisition_mode != "1D-Chrono")\
                and (self.current_camera_settings.acquisition_mode != "1D-Chrono-Live")\
                and (self.current_camera_settings.acquisition_mode != "2D-Chrono"):
            # self.__frame_number += 1
            self.has_data_event.set()

    @property
    def sensor_dimensions(self) -> (int, int):
        return self.__sensor_dimensions

    @property
    def readout_area(self) -> (int, int, int, int):
        return self.__readout_area

    @readout_area.setter
    def readout_area(self, readout_area_TLBR: (int, int, int, int)) -> None:
        self.__readout_area = readout_area_TLBR
        print(readout_area_TLBR)

    @property
    def flip(self):
        return False

    @flip.setter
    def flip(self, do_flip):
        pass

    def start_live(self) -> None:
        api_broker = PlugInManager.APIBroker()
        api = api_broker.get_api(version='~1.0', ui_version='~1.0')
        self.__data_item_display = api.library.get_data_item_for_reference_key(self.camera_id)

        self.__frame_number = 0
        self.sizex, self.sizey = self.camera.getImageSize()
        if self.current_camera_settings.acquisition_style == "1d":
            self.sizey = 1
        print(f"Start live, Image size: {self.sizex} x {self.sizey}"
              f"  twoD: {self.current_camera_settings.acquisition_style}"
              f"    mode: {self.current_camera_settings.acquisition_mode}"
              f"    nb spectra {self.current_camera_settings.spectra_count}")
        self.camera.setAccumulationNumber(self.current_camera_settings.spectra_count)
        hardware_source = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
            self.camera_id)

        if "Chrono" in self.current_camera_settings.acquisition_mode:
            self.sizez = 1
            if (self.current_camera_settings.acquisition_mode == "2D-Chrono"):
                self.sizez = self.current_camera_settings.spectra_count
                self.spimimagedata = numpy.zeros((self.sizez, self.sizey, self.sizex), dtype = numpy.float32)
            else:
                self.sizey = self.current_camera_settings.spectra_count
                self.sizez = 1
                self.spimimagedata = numpy.zeros((self.sizey, self.sizex), dtype=numpy.float32)
            self.spimimagedata_ptr = self.spimimagedata.ctypes.data_as(ctypes.c_void_p)
            self.camera.startSpim(self.current_camera_settings.spectra_count, 1,
                                  self.current_camera_settings.exposure_ms * 1000,
                                  self.current_camera_settings.acquisition_mode == "2D-Chrono")
            self.camera.resumeSpim(4)  # stop eof
            if self.current_camera_settings.acquisition_mode == "1D-Chrono-Live":
                self.camera.setSpimMode(1)  # continuous
            # for channels in hardware_source.data_channels:
            #     channels.processor = "None"
        elif "spim" in self.current_camera_settings.acquisition_mode:
            pass
        else:
            self.sizez = 1
            acqmode = 0
            if self.current_camera_settings.acquisition_mode == "Cumul":
                acqmode = 1
                self.imagedata = numpy.zeros((self.sizey, self.sizex), dtype=numpy.float32)
            else:
                self.imagedata = numpy.zeros((self.sizey, self.sizex), dtype=numpy.uint16)
            self.imagedata_ptr = self.imagedata.ctypes.data_as(ctypes.c_void_p)
            self.__acqon = self.camera.startFocus(self.current_camera_settings.exposure_ms * 1000,
                                                  self.current_camera_settings.acquisition_style, acqmode)
            # for channels in hardware_source.data_channels:
            #     channels. = HardwareSource.SumProcessor(((0.25, 0.0), (0.5, 1.0)))
            #     pass
        self._last_time = time.time()

    def stop_live(self) -> None:
        if "Chrono" in self.current_camera_settings.acquisition_mode:
            self.camera.stopSpim(True)
            self.has_data_event.set()
            self.__acqon = False
        else:
            if self.__acqspimon:
                self.has_spim_data_event.set()
            else:
                self.__acqon = self.camera.stopFocus()

    def acquire_image(self) -> dict:
        gotit = self.has_data_event.wait(1)
        self.has_data_event.clear()
        if "Chrono" in self.current_camera_settings.acquisition_mode:
            data = self.spimimagedata
            if "2D" in self.current_camera_settings.acquisition_mode:
                collection_dimensions = 1
                datum_dimensions = 2
            else:
                collection_dimensions = 0
                datum_dimensions = 2
        else:
            data = self.imagedata
            if data.shape[0] == 1:
                datum_dimensions = 1
                collection_dimensions = 1
            else:
                datum_dimensions = 2
                collection_dimensions = 0
        properties = dict()
        properties["frame_number"] = self.__frame_number
        properties["acquisition_mode"] = self.current_camera_settings.acquisition_mode
        return {"data": data, "collection_dimension_count": collection_dimensions, "datum_dimension_count": datum_dimensions, "properties": properties}

    @property
    def calibration_controls(self) -> dict:
        """Define the AS2 calibration controls for this camera.

        The controls should be unique for each camera if there are more than one.
        """
        return self.__calibration_controls

    @calibration_controls.setter
    def calibrations_controls(self, value: dict):
        """ Instrument owner will give controls names, override default camera eels calibration"""
        self.__calibration_controls = value

    @property
    def processing(self) -> typing.Optional[str]:
        return self.__processing

    @processing.setter
    def processing(self, value: str) -> None:
        self.__processing = value

    def get_expected_dimensions(self, binning: int) -> (int, int):
        return self.__sensor_dimensions

    def acquire_sequence_prepare(self, scansize) -> None:
        self.__frame_number = 0
        print(f"preparing spim acquisition")
        self.__twoD = self.current_camera_settings.processing == "sum_project"
        self.current_camera_settings.processing = "None"
        if self.__twoD:
            self.sizex, self.sizey = self.camera.getImageSize()
            self.sizez = scansize
        else:
            self.sizex, tmpy = self.camera.getImageSize()
            self.sizey = scansize
            self.sizez = 1
        print(f"{self.sizex} {self.sizey} {self.sizez}")
        self.spimimagedata = numpy.zeros((self.sizey * self.sizez, self.sizex), dtype = numpy.float32)
        self.spimimagedata = numpy.ascontiguousarray(self.spimimagedata, dtype = numpy.float32)
        self.spimimagedata_ptr = self.spimimagedata.ctypes.data_as(ctypes.c_void_p)
        print(f"allocated {self.spimimagedata_ptr}")
        if self.__acqon:
            self.camera.stopFocus()
        self.camera.startSpim(self.sizey * self.sizez, 1, self.current_camera_settings.exposure_ms * 1000, self.__twoD)
        print(f"prepared")

    def acquire_sequence(self, n: int) -> dict:
        self.camera.resumeSpim(4)  # stop eof
        self.__acqspimon = True
        print(f"resumed")
        print(f"acquiring {n}")
        gotit = self.has_spim_data_event.wait(10000.0)
        self.has_spim_data_event.clear()
        self.camera.stopSpim(True)
        self.__acqspimon = False
        data = self.spimimagedata
        self.camera.setBinning(self.__orsay_binning[0], self.__orsay_binning[1])  # restore, this is only needed until regular binning is used instead of orsay binning
        properties = dict()
        properties["frame_number"] = self.__frame_number
        properties["acquisition_mode"] = "spim"
        return {"data": data, "properties": properties}

    def acquire_sequence_orsay(self, mode = 4) -> None:
        self.camera.resumeSpim(mode)  # stop eof
        self.__acqspimon = True
        print(f"resumed")
        print(f"acquisition mode {mode}")

    def start_monitor(self) -> None:
        pass

    # custom methods (not part of the camera_base.Camera)

    @property
    def fan_enabled(self) -> bool:
        return self.camera.getFan()

    @fan_enabled.setter
    def fan_enabled(self, value: bool) -> None:
        self.camera.setFan(bool(value))
        pass

    def isCameraAcquiring(self):
        # acqon = self.camera.getCCDStatus()[0] != "idle"
        return self.__acqon

    def __getTurboMode(self):
        value, hs, vs = self.camera.getTurboMode()
        print(f"turbo mode : {value}")
        return value

    @property
    def readoutTime(self) -> float:
        return self.camera.getReadoutTime()

    def get_acquire_sequence_metrics(self, camera_frame_parameters: typing.Dict) -> typing.Dict:
        acquisition_frame_count = camera_frame_parameters.get("acquisition_frame_count")
        storage_frame_count = camera_frame_parameters.get("storage_frame_count")
        frame_time = self.current_camera_settings.exposure_ms * 1000 + self.camera.getReadoutTime()
        acquisition_time = frame_time * acquisition_frame_count
        if camera_frame_parameters.get("processing") == "sum_project":
            acquisition_memory = self.camera.getImageSize()[0] * 4 * acquisition_frame_count
            storage_memory = self.camera.getImageSize()[0] * 4 * storage_frame_count
        else:
            acquisition_memory = self.camera.getImageSize()[0] * self.camera.getImageSize()[1] * 4 * acquisition_frame_count
            storage_memory = self.camera.getImageSize()[0] * self.camera.getImageSize()[1] * 4 * storage_frame_count
        return { "acquisition_time": acquisition_time, "acquisition_memory": acquisition_memory, "storage_memory": storage_memory }


class CameraFrameParameters(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self
        self.exposure_ms = self.get("exposure_ms", 125)  # milliseconds
        self.h_binning = self.get("h_binning", 1)
        self.v_binning = self.get("v_binning", 1)
        self.acquisition_style = self.get("acquisition_style", "1d")  # 1d, 2d
        self.acquisition_mode = self.get("acquisition_mode", "Focus")  # Focus, Cumul, 1D-Chrono, 1D-Chrono-Live, 2D-Chrono
        self.spectra_count = self.get("spectra_count", 1)
        self.speed = self.get("speed", 1)
        self.gain = self.get("gain", 0)
        self.multiplication = self.get("multiplication", 1)
        self.port = self.get("port", 0)
        self.area = self.get("area", (0, 0, 2048, 2048))  # a tuple: top, left, bottom, right
        self.turbo_mode_enabled = self.get("turbo_mode_enabled", False)
        self.video_threshold = 0
        self.integration_count = 1  # required

    def __copy__(self):
        return self.__class__(copy.copy(dict(self)))

    def __deepcopy__(self, memo):
        deepcopy = self.__class__(copy.deepcopy(dict(self)))
        memo[id(self)] = deepcopy
        return deepcopy

    # @property
    # def exposure_ms(self):
    #     return self.exposure_ms
    #
    # @exposure_ms.setter
    # def exposure_ms(self, value):
    #     self.exposure_ms = value

    @property
    def binning(self):
        return self.h_binning

    @binning.setter
    def binning(self, value):
        self.h_binning = value

    def as_dict(self):
        return {
            "exposure_ms": self.exposure_ms,
            "h_binning": self.h_binning,
            "v_binning": self.v_binning,
            "acquisition_style": self.acquisition_style,
            "acquisition_mode": self.acquisition_mode,
            "spectra_count": self.spectra_count,
            "speed": self.speed,
            "gain": self.gain,
            "multiplication": self.multiplication,
            "port": self.port,
            "area": self.area,
            "turbo_mode_enabled": self.turbo_mode_enabled,
            "video_threshold": self.video_threshold
        }


from nion.utils import Event

class CameraSettings:

    def __init__(self, camera_device: CameraDevice):
        # these events must be defined
        self.current_frame_parameters_changed_event = Event.Event()
        self.record_frame_parameters_changed_event = Event.Event()
        self.profile_changed_event = Event.Event()
        self.frame_parameters_changed_event = Event.Event()

        # the list of possible modes should be defined here
        self.modes = ["Focus", "Cumul", "1D-Chrono","1D-Chrono-Live", "2D-Chrono"]

        self.__camera_device = camera_device

    def close(self):
        pass

    def initialize(self, **kwargs):
        pass

    def apply_settings(self, settings_dict: typing.Dict) -> None:
        pass

    def get_frame_parameters_from_dict(self, d):
        return CameraFrameParameters(d)

    def set_current_frame_parameters(self, frame_parameters: CameraFrameParameters) -> None:
        self.__camera_device.current_camera_settings = frame_parameters
        self.current_frame_parameters_changed_event.fire(frame_parameters)
        self.record_frame_parameters_changed_event.fire(frame_parameters)

    def get_current_frame_parameters(self) -> CameraFrameParameters:
        return self.__camera_device.current_camera_settings

    def set_record_frame_parameters(self, frame_parameters: CameraFrameParameters) -> None:
        self.set_current_frame_parameters(frame_parameters)

    def get_record_frame_parameters(self) -> CameraFrameParameters:
        return self.get_current_frame_parameters()

    def set_frame_parameters(self, profile_index: int, frame_parameters) -> None:
        self.set_current_frame_parameters(frame_parameters)

    def get_frame_parameters(self, profile_index: int):
        return self.get_current_frame_parameters()

    def set_selected_profile_index(self, profile_index: int) -> None:
        pass

    @property
    def selected_profile_index(self) -> int:
        return 0

    def get_mode(self) -> str:
        return str()

    def set_mode(self, mode: str) -> None:
        pass

    def open_configuration_interface(self, api_broker) -> None:
        pass

    def open_monitor(self) -> None:
        pass


class CameraModule:

    def __init__(self, stem_controller_id: str, camera_device: CameraDevice, camera_settings: CameraSettings):
        self.stem_controller_id = stem_controller_id
        self.camera_device = camera_device
        self.camera_settings = camera_settings
        self.camera_panel_type = "orsay_camera_panel"


def periodic_logger():
    messages = list()
    data_elements = list()
    return messages, data_elements


def run():
    # input("Time to attach debugger -- type return to continue")

    camera_device = CameraDevice(1, "KURO: 2048B", "", True)
    camera_device.camera_type = "eels"
    camera_device.camera_id = "orsay_camera_kuro"
    camera_device.camera_name = _("Orsay KURO")

    camera_settings = CameraSettings(camera_device)

    Registry.register_component(CameraModule("autostem_controller", camera_device, camera_settings), {"camera_module"})

    camera_device2 = CameraDevice(1, "ProEM+: 1600xx(2)B eXcelon",  "", True)
    camera_device2.camera_type = "eire"
    camera_device2.camera_id = "orsay_camera_eire"
    camera_device2.camera_name = _("Orsay ProEM")

    camera_settings2 = CameraSettings(camera_device2)

    Registry.register_component(CameraModule("autostem_controller", camera_device2, camera_settings2), {"camera_module"})


