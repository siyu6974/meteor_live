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


def main():
    config = configparser.ConfigParser()
    config.read('settings.ini')

    processor = Processor(config)
    processor.streamer = None
    processor.run()
    cap = cv.VideoCapture('/Volumes/HyperDrive/yezi_perseids/C5513.MP4')

    ctr = 0

    while cap.isOpened():
        # print(ctr)
        ctr += 1
        ret, frame = cap.read()
        # cv.imshow('live', frame)
        # frame = cv.resize(frame, (1304, 976))
        frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        processor.push_frame(frame)
        # print(ctr)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break


if __name__ == '__main__':
    main()
