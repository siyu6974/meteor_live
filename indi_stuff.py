import logging
import sys
import time
import io
import PyIndi
from PyIndi import INumberVectorProperty
import PIL.Image as Image
import numpy as np
import cv2 as cv

# logging.basicConfig(filename='logfile.log', level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)


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
    def __init__(self, host_adr='localhost', port=7624):
        super(IndiClient, self).__init__()
        self.logger = logging.getLogger('IndiClient')
        self.logger.info('creating an instance of IndiClient')

        self.setServer(host_adr, port)
        self.connectServer()

        self.cam = None
        self._gain = 200
        self._exp = 0.04
        self.img_ctr = 0

        self.test = None

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
        self.img_ctr += 1
        self.logger.info(f"img count {self.img_ctr}")

        img = np.array(bp.getblobdata()).reshape((976, 1304))
        img = Image.fromarray(img)
        # img = Image.fromarray(cv.cvtColor(img, cv.COLOR_BAYER_BG2BGR))
        img.save(f'frames/frame{self.img_ctr}.png')

    def newSwitch(self, svp):
        self.logger.info(f"new Switch {svp.name} for device {svp.device}")

    def newNumber(self, nvp):
        if 'CCD' in nvp.name:
            self.logger.info(f"{nvp.name} on {nvp.device} is now {[vp.value for vp in nvp]}")
        if nvp.name == 'CCD_EXPOSURE' and nvp[0].value == 0:
            self.take_exposure()

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
    def set_gain(self, gain: float):
        self._gain = gain
        controls = self.cam.getNumber('CCD_CONTROLS')
        controls[0].value = self._gain
        self.sendNewNumber(controls)

    def set_exp(self, exp: float):
        self._exp = exp
        exp = self.cam.getNumber("STREAMING_EXPOSURE")
        exp[0].value = self._exp
        self.sendNewNumber(exp)

    def start_streaming(self):
        stream = self.cam.getSwitch("CCD_VIDEO_STREAM")
        stream[0].s = PyIndi.ISS_ON
        stream[1].s = PyIndi.ISS_OFF
        self.sendNewSwitch(stream)
        print("=======start streaming=============")

    def stop_streaming(self):
        stream = self.cam.getSwitch("CCD_VIDEO_STREAM")
        stream[0].s = PyIndi.ISS_OFF
        stream[1].s = PyIndi.ISS_ON
        self.sendNewSwitch(stream)
        print("=======stop streaming=============")

