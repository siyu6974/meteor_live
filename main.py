import PyIndi
import time
import sys
import threading
import datetime
import numpy as np
import logging
from indi_stuff import Device, IndiClient
import io
import configparser
from streamer import Streamer
import atexit
from utils import exit_handler

# logging.basicConfig(filename='logfile.log', level=logging.DEBUG)
# logging.basicConfig(level=logging.WARN)


config = configparser.ConfigParser()
config.read('settings.ini')

# connect the server
indiclient = IndiClient(config)
streamer = Streamer(config)
indiclient.newFrameCB = streamer.push_frame
atexit.register(exit_handler, indiclient=indiclient)


while indiclient.cam is None:
    time.sleep(0.1)

time.sleep(5)
indiclient.stop_streaming()
indiclient.set_exp()
indiclient.set_gain()
indiclient.start_streaming()
streamer.run()

while True:
    time.sleep(1)

