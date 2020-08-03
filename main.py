import PyIndi
import time
import sys
import threading
from skyfield.api import Topos, load, utc
import datetime
import numpy as np
import logging
from indi_stuff import Device, IndiClient
import io

# logging.basicConfig(filename='logfile.log', level=logging.DEBUG)
logging.basicConfig(level=logging.WARN)


# connect the server
indiclient = IndiClient()

while True:
    if indiclient.cam is not None:
        indiclient.set_exp(0.04)
        indiclient.set_gain(50)
        indiclient.start_streaming()
        break

    time.sleep(0.1)

while True:
    time.sleep(1)

