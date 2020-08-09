import logging
import time
import PyIndi
from PyIndi import INumberVectorProperty
import numpy as np
from utils import FPS

# logging.basicConfig(filename='logfile.log', level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)


class Device(PyIndi.BaseDevice):
    def getNumber(self, property_name) -> INumberVectorProperty:
        property_value = super().getNumber(property_name)
        while not property_value:
            time.sleep(0.01)
            property_value = super().getNumber(property_name)
        return property_value

    def getSwitch(self, property_name):
        property_value = super().getSwitch(property_name)
        while not property_value:
            time.sleep(0.01)
            property_value = super().getSwitch(property_name)
        return property_value


class IndiClient(PyIndi.BaseClient):
    def __init__(self, config, host_adr='localhost', port=7624):
        super(IndiClient, self).__init__()
        self.logger = logging.getLogger('IndiClient')
        self.logger.info('creating an instance of IndiClient')

        self.setServer(host_adr, port)
        self.connectServer()

        self.cam = None
        self._gain = int(config['capture']['gain'])
        self._exp = float(config['capture']['exposure'])

        self.img_ctr = 0
        self._img_w = int(config['capture']['size_w'])
        self._img_h = int(config['capture']['size_h'])

        self.fps = FPS(30)

        self.newFrameCB = None

    def getDevice(self, device_name) -> Device:
        device = super().getDevice(device_name)
        while not device:
            time.sleep(0.01)
            device = super().getDevice(device_name)
        device.__class__ = Device
        return device

    def newDevice(self, d):
        if 'CCD' in d.getDeviceName():
            self.cam = d

    def newProperty(self, p):
        if self.cam is not None and p.getName() == "CONNECTION" and p.getDeviceName() == self.cam.getDeviceName():
            self.connectDevice(self.cam.getDeviceName())
            self.setBLOBMode(PyIndi.B_ALSO, self.cam.getDeviceName(), None)

    def removeProperty(self, p):
        pass

    def newBLOB(self, bp):
        self.logger.debug(f"img count {self.img_ctr}")
        self.img_ctr += 1

        self.fps.count()
        img = np.array(bp.getblobdata()).reshape((self._img_h, self._img_w))
        if self.newFrameCB:
            self.newFrameCB(img)

    def newSwitch(self, svp):
        self.logger.info(f"new Switch {svp.name} for device {svp.device}")

    def newNumber(self, nvp):
        if 'CCD' in nvp.name:
            self.logger.info(f"{nvp.name} on {nvp.device} is now {[vp.value for vp in nvp]}")

    def newText(self, tvp):
        self.logger.info(f"new Text {tvp.name} for device {tvp.device}")

    def newLight(self, lvp):
        self.logger.info(f"new Light {lvp.name} for device {lvp.device}")

    def newMessage(self, d, m):
        self.logger.info(f"new Message {d.messageQueue(m)}")

    def serverConnected(self):
        self.logger.info(f"Server connected ({self.getHost()}): {str(self.getPort())}")

    def serverDisconnected(self, code):
        self.logger.info(f"Server disconnected (exit code = {str(code)},{str(self.getHost())}:{str(self.getPort())}")

    # =====================
    # Camera
    def set_gain(self, gain: float = None):
        if gain is not None:
            self._gain = gain
        controls = self.cam.getNumber('CCD_CONTROLS')
        controls[0].value = self._gain
        self.sendNewNumber(controls)

    def set_exp(self, exp: float = None):
        if exp is not None:
            self._exp = exp
        exp = self.cam.getNumber("STREAMING_EXPOSURE")
        exp[0].value = self._exp
        self.sendNewNumber(exp)

    def start_streaming(self):
        stream = self.cam.getSwitch("CCD_VIDEO_STREAM")
        stream[0].s = PyIndi.ISS_ON
        stream[1].s = PyIndi.ISS_OFF
        self.sendNewSwitch(stream)
        self.logger.info("=======start streaming=============")

    def stop_streaming(self):
        stream = self.cam.getSwitch("CCD_VIDEO_STREAM")
        stream[0].s = PyIndi.ISS_OFF
        stream[1].s = PyIndi.ISS_ON
        self.sendNewSwitch(stream)
        self.logger.info("=======stop streaming=============")
