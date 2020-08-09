import time
import sys
import threading
import datetime
import numpy as np
import logging
import io
import configparser
from streamer import Streamer
import atexit
from utils import exit_handler
from post_process import Processor
import cv2 as cv
# logging.basicConfig(filename='logfile.log', level=logging.DEBUG)
# logging.basicConfig(level=logging.WARN)
from multiprocessing import Queue, Process


config = configparser.ConfigParser()
config.read('settings.ini')

streamer = Streamer(config)
processor = Processor(config)
processor.streamer = streamer
streamer.run()
processor.run()
cap = cv.VideoCapture('test.mp4')

ctr = 0

while cap.isOpened():
    # print(ctr)
    ctr += 1
    ret, frame = cap.read()
    # cv.imshow('live', frame)
    frame = cv.resize(frame, (1304, 976))
    frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    processor.push_frame(frame)

    if cv.waitKey(30) & 0xFF == ord('q'):
        break




