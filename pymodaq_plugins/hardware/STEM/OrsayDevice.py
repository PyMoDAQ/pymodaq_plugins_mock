# standard libraries
import copy
import ctypes
import gettext
import numpy
import threading
import typing
# third party libraries

# local libraries
from nion.swift.model import HardwareSource
from nion.utils import Registry

from .orsayscan import orsayScan, LOCKERFUNC, UNLOCKERFUNC, UNLOCKERFUNCA
from . ConfigDialog import ConfigDialog

from nion.instrumentation import scan_base

_ = gettext.gettext


AUTOSTEM_CONTROLLER_ID = "autostem_controller"


class Device:

    def __init__(self):
        # these are required to register the device
        self.scan_device_id = "orsay_scan_device"
        self.scan_device_name = _("Orsay Scan")
        self.stem_controller_id = AUTOSTEM_CONTROLLER_ID

        self.__is_scanning = False
        self.on_device_state_changed = None
        self.flyback_pixels = 0
        self.__frame_number = 0
        self.__scan_size = [512, 512]
        self.__sizez = 2
        self.orsayscan = orsayScan(1)
        self.spimscan = orsayScan(2, self.orsayscan.orsayscan)
        #list all inputs
        totalinputs = self.orsayscan.getInputsCount()
        self.dinputs = dict()
        for index in range(totalinputs):
            prop = self.orsayscan.getInputProperties(index)
            self.dinputs[index] = [prop, False]
        self.usedinputs = [[0, False, self.dinputs[0][0]], [1, False, self.dinputs[1][0]], [6, False, self.dinputs[6][0]], [7, False, self.dinputs[7][0]]]
        self.orsayscan.SetInputs([1, 0])
        __inputs = self.orsayscan.GetInputs()
        for inp in __inputs[1]:
            for k in self.usedinputs:
                if k[0] == inp:
                    k[1] = True
        #
        # Add eels camera if there
        #
        self.__eelscamera = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_camera_kuro")
        self.usedinputs.append([100, False, [0, 0, "eels", 100]])
        channels = list(self.usedinputs[ch][1] for ch in range(len(self.usedinputs)))
        self.__cameras_parsed = False

        self.__profiles = list()
        self.__profiles.append(scan_base.ScanFrameParameters({"size": (512, 512), "pixel_time_us": 0.2, "channels":channels}))
        self.__profiles.append(scan_base.ScanFrameParameters({"size": (1024, 1024), "pixel_time_us": 0.2, "channels":channels}))
        self.__profiles.append(scan_base.ScanFrameParameters({"size": (64, 64), "pixel_time_us": 1000, "channels":channels}))
        self.__profiles.append(scan_base.ScanFrameParameters({"size": (2048, 2048), "pixel_time_us": 2.5, "channels":channels}))
        self.__frame_parameters = copy.deepcopy(self.__profiles[0])

        self.imagedata = numpy.empty((self.__sizez * self.__scan_size[1], self.__scan_size[0]), dtype = numpy.int16)
        self.imagedata_ptr = self.imagedata.ctypes.data_as(ctypes.c_void_p)
        self.has_data_event = threading.Event()
        self.fnlock = LOCKERFUNC(self.__data_locker)
        self.orsayscan.registerLocker(self.fnlock)
        self.fnunlock = UNLOCKERFUNCA(self.__data_unlockerA)
        self.orsayscan.registerUnlockerA(self.fnunlock)
        self.orsayscan.pixelTime = 0.000002
        # set the scan scale to 5v to match SuperScan, which output bank, then one for each direction
        self.orsayscan.setScanScale(0, 5.0, 5.0)
        #for channel_index in range(self.channel_count):
        #    self.set_channel_enabled(channel_index, channels_enabled[channel_index])

        print(f"OrsayScan Version: {self.orsayscan._major}")
        self.__angle = 0

    def close(self):
        pass

    def change_pmt(self, channel_index: int, increase: bool) -> None:
        """Change the PMT value for the give channel; increase or decrease only."""
        pass

    @property
    def current_frame_parameters(self) -> scan_base.ScanFrameParameters:
        return self.__frame_parameters

    @property
    def channel_count(self):
        # if not self.__cameras_parsed:
        #     self.__eelscamera = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
        #         "orsay_camera_kuro")
        #     if self.__eelscamera is not None:
        #         self.usedinputs.append([100, False, [0, 0, "eels", 100]])
        #         channels = list(self.usedinputs[ch][1] for ch in range(len(self.usedinputs)))
        # self.__cameras_parsed = True
        return len(self.usedinputs)

    @property
    def channels_enabled(self) -> typing.Tuple[bool, ...]:
        #return tuple(self.dinputs[l][1] for l in range(len(self.dinputs)))
        return self.__frame_parameters.channels

    def set_channel_enabled(self, channel_index: int, enabled: bool) -> bool:
        """in 16-bit mode, the number of channels used in hardware needs to be even
        in case odd number is selected, last channels can be repeated twice.
        call back function should then ignore this last channel; and it will match user interface
        in 32-bit mode, one channel can be enabled"""
        assert 0 <= channel_index < self.channel_count
        #self.dinputs[channel_index][1] = enabled
        changed = self.__frame_parameters.channels[channel_index] != enabled
        self.__frame_parameters.channels[channel_index] = enabled
        return changed

    def get_channel_name(self, channel_index: int) -> str:
        #return self.orsayscan.getInputProperties(self.usedinputs[channel_index])[2]
        return self.usedinputs[channel_index][2][2]

    def read_partial(self, frame_number, pixels_to_skip) -> (typing.Sequence[dict], bool, bool, tuple, int, int):
        """Read or continue reading a frame.

        The `frame_number` may be None, in which case a new frame should be read.

        The `frame_number` otherwise specifies which frame to continue reading.

        The `pixels_to_skip` specifies where to start reading the frame, if it is a continuation.

        Return values should be a list of dict's (one for each active channel) containing two keys: 'data' and
        'properties' (see below), followed by a boolean indicating whether the frame is complete, a boolean indicating
        whether the frame was bad, a tuple of the form (top, left), (height, width) indicating the valid sub-area
        of the data, the frame number, and the pixels to skip next time around if the frame is not complate.

        The 'data' keys in the list of dict's should contain a ndarray with the size of the full acquisition and each
        ndarray should be the same size. The 'properties' keys are dicts which must contain the frame parameters and
        a 'channel_id' indicating the index of the channel (may be an int or float).
        """

        gotit = self.has_data_event.wait(2.0)
        #if gotit:
        frame_number = self.__frame_number

        _data_elements = []

        sub_area = None
        channel_index = 0
        dataposition = 0

        for l in self.__frame_parameters.channels:
            if l:
                data_element = dict()
                image_metadata = self.__frame_parameters.as_dict()
                if self.usedinputs[channel_index][0] < 100:
                    data_array = self.imagedata[dataposition*self.__scan_size[1]:(dataposition+1)*self.__scan_size[1], 0:self.__scan_size[0]].astype(numpy.float32)
                    sub_area = ((0, 0), data_array.shape)
                else:
                    if self.isSpim and (self.__eelscamera is not None):
                        data_array = self.__eelscamera.spimimagedata
                        data_array.shape = (self.__scan_size[1], self.__scan_size[0], -1)
                        image_metadata["sub_area"] =  ((0, 0, 0), data_array.shape)
                        data_element["collection_dimension_count"] = 2
                        data_element["datum_dimension_count"] = 1
                        sub_area = ((0, 0, 0), data_array.shape)
                dataposition = dataposition + 1
                image_metadata["pixel_time_us"] = float(self.orsayscan.pixelTime * 1E6)
                image_metadata["pixels_x"] = self.__scan_size[1]
                image_metadata["pixels_y"] = self.__scan_size[0]
                image_metadata["center_x_nm"] = 0
                image_metadata["center_y_nm"] = 0
                image_metadata["rotation_deg"] = 0
                image_metadata["channel_id"] = channel_index
                data_element["data"] = data_array
                data_element["properties"] = image_metadata
                _data_elements.append(data_element)
            channel_index = channel_index + 1

        complete = True
        bad_frame = False
        self.has_data_event.clear()
        pixels_to_skip = 0  # only important when sub_area is not full area
        return _data_elements, complete, bad_frame, sub_area, frame_number, pixels_to_skip
        #else:
        #    return None, False, False, None, 0,0

    def get_profile_frame_parameters(self, profile_index: int) -> scan_base.ScanFrameParameters:
        return copy.deepcopy(self.__profiles[profile_index])

    @property
    def is_scanning(self) -> bool:
        self.__is_scanning = (self.orsayscan.getImagingKind() != 0)
        return self.__is_scanning

    def show_configuration_dialog(self, api_broker, document_controller) -> None:
        """Open settings dialog, if any."""
        api = api_broker.get_api(version="~1.0")
        myConfig = ConfigDialog(document_controller)
        #pass

    def save_frame_parameters(self) -> None:
        """Called when shutting down. Save frame parameters to persistent storage."""
        pass

    def set_frame_parameters(self, frame_parameters: scan_base.ScanFrameParameters) -> None:
        """Called just before and during acquisition.
        Device should use these parameters for new acquisition; and update to these parameters during acquisition.
        """
        needrestart = self.__is_scanning
        if self.__frame_parameters.rotation_rad != frame_parameters.rotation_rad:
            if needrestart:
                self.cancel()
            self.orsayscan.setScanRotation(frame_parameters.rotation_rad)
            #print(self.orsayscan.getScanRotation())
            if needrestart:
                self.start_frame(True)
        self.orsayscan.pixelTime = frame_parameters.pixel_time_us / 1E6
        if self.__frame_parameters.size != frame_parameters.fov_nm:
            if needrestart:
                self.cancel()
            self.orsayscan.SetFieldSize(frame_parameters.fov_nm*1e-9)
            if needrestart:
                self.start_frame(True)

        if self.__frame_parameters.size != frame_parameters.size:
            if needrestart:
                self.cancel()
            #print("Changing frame size to [" + str(frame_parameters.size[0]) + ", " + str(frame_parameters.size[1]) + "]");
            self.orsayscan.setImageSize(frame_parameters.size[1], frame_parameters.size[0])
            if needrestart:
                self.start_frame(True)
        self.__frame_parameters = copy.deepcopy(frame_parameters)

    def set_profile_frame_parameters(self, profile_index: int, frame_parameters: scan_base.ScanFrameParameters) -> None:
        """Set the acquisition parameters for the give profile_index (0, 1, 2)."""
        self.__profiles[profile_index] = copy.deepcopy(frame_parameters)

    def set_idle_position_by_percentage(self, x: float, y: float) -> None:
        """Set the idle position as a percentage of the last used frame parameters."""
        pass

    def start_frame(self, is_continuous: bool) -> int:
        """Start acquiring. Return the frame number."""
        if not self.__is_scanning:
            __inputs = []
            self.isSpim = False

            pos = 0
            for l in self.__frame_parameters.channels:
                #if l[1][1]:
                if l:
                    self.isSpim = self.usedinputs[pos][0] >= 100
                    if not self.isSpim:
                        __inputs.append(self.usedinputs[pos][0])
                pos = pos + 1
            lg = len(__inputs)
            #
            # si le nombre d'entrée est plus grand que 1, il doit être pair!
            # limitation du firmware.
            #
            if lg > 0:
                if lg % 2:
                    __inputs.append(6)
                self.orsayscan.SetInputs(__inputs)
            self.__scan_size = self.orsayscan.getImageSize()
            self.__sizez = self.orsayscan.GetInputs()[0]
            if self.__sizez % 2:
                self.__sizez += 1
            self.imagedata = numpy.empty((self.__sizez * self.__scan_size[1], self.__scan_size[0]), dtype = numpy.int16)
            self.imagedata_ptr = self.imagedata.ctypes.data_as(ctypes.c_void_p)
            self.__angle = 0
            self.orsayscan.setScanRotation(self.__angle)

            if self.isSpim:
                self.__eelscamera = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id("orsay_camera_kuro").camera
                if self.__eelscamera is not None:
                    self.__eelscamera.acquire_sequence_prepare(self.__scan_size[1] * self.__scan_size[0])
            self.__is_scanning = self.orsayscan.startImaging(0, 1)
            if self.isSpim:
                self.__eelscamera.acquire_sequence_orsay(4)
            self.__frame_number = 0
        return self.__frame_number

    def cancel(self) -> None:
        """Cancel acquisition (immediate)."""
        self.orsayscan.stopImaging(True)
        self.__is_scanning = False

    def stop(self) -> None:
        """Stop acquiring."""
        self.orsayscan.stopImaging(False)
        #self.__is_scanning = False

    def __data_locker(self, gene, datatype, sx, sy, sz):
        sx[0] = self.__scan_size[0]
        sy[0] = self.__scan_size[1]
        sz[0] = self.__sizez
        datatype[0] = 2
        return self.imagedata_ptr.value

    def __data_unlocker(self, gene, newdata):
        self.has_data_event.set()

    def __data_unlockerA(self, gene, newdata, imagenb, rect):
        if newdata:
            # message = "Image: " + str(imagenb) + "   pos: [" + str(rect[0]) + ", " + str(rect[1]) + "]   size: [" + str(rect[2]) + ", " + str(rect[3]) + "]"
            # print (message)
            # rect[0] x corner of rectangle updated
            # rect[1] y corner of rectangle updated
            # rect[2] horizontal size of the rectangle.
            # rect[3] vertical size of the rectangle.
            # image has all its data if .
            # numpy may only take the rectangle.
            # if rect[1] + rect[3] == self.__scan_size[1]:
            #     self.__angle = self.__angle + 5
            #     self.orsayscan.setScanRotation(self.__angle)
            #     print("Frame number: " + str(imagenb) + "    New rotation: " + str(self.__angle))
            self.__frame_number = imagenb
            self.has_data_event.set()
            if self.isSpim:
                status = self.__eelscamera.camera.getCCDStatus()
                if status["mode"] == "idle":
                    hardware_source = HardwareSource.HardwareSourceManager().get_hardware_source_for_hardware_source_id(
                        self.scan_device_id)
                    hardware_source.stop_playing()


def run():
    scan_device = Device()
    component_types = {"scan_device"}  # the set of component types that this component represents
    Registry.register_component(scan_device, component_types)
