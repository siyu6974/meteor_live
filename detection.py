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
from post_process import *


def saveMeteor(buffer, fps, frame_no):
    size = buffer[0]['img'].shape
    fourcc = cv.VideoWriter_fourcc('H', '2', '6', '4')
    vw = cv.VideoWriter(f"frm_{frame_no}.mkv", fourcc,
                        fps, size[::-1])

    for i, obj in enumerate(buffer):
        img = obj['img']
        img = cv.cvtColor(img, cv.COLOR_BAYER_BG2BGR)
        vw.write(img)
    vw.release()
    print("--------------saving DONE--------------")

class Processor:
    def __init__(self, conf, dark=None):
        self._dark = dark
        self._threshold = 50
        self.global_events = {}
        self._fps = 1 / float(conf['capture']['exposure'])
        self._runningAvg = np.zeros((int(conf['capture']['size_h']), int(conf['capture']['size_w'])), dtype=np.float32)
        self._buffer = ImageBuffer(int(self._fps*5))
        self._prev = None
        
        self.mask = None
        if 'mask' in conf['capture']:
            self.mask = cv.threshold(cv.imread(conf['capture']['mask'], 0), 120, 255, cv.THRESH_BINARY)[1]


    def process(self, img: np.array, frame_no=None):
        if self._dark:
            img -= cv.absdiff(img, self._dark)
        self._buffer.add(img)

        # cur = np.float32(img)
        cur = cv.cvtColor(img, cv.COLOR_BAYER_RG2GRAY)
#         print(img.dtype)

        if self.mask is not None:
            cur = cv.bitwise_and(img, img, mask=self.mask)
#         print(cur.dtype)

        if self._prev is not None:
            prev = self._prev
        else:
            prev = cur

        # smooth
        cur = cv.medianBlur(cur, 3)
        diff = cv.absdiff(cur, prev)
#         diff = cur - prev
        cv.imshow("Diff image", diff)

        _, diff_bin = cv.threshold(diff, 20, 255, cv.THRESH_BINARY)
        self._prev = cur
        cv.accumulateWeighted(diff_bin, self._runningAvg, 0.2)


        avg_img_int = cv.convertScaleAbs(self._runningAvg)
        contours, hierarchy = cv.findContours(avg_img_int, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        for c in contours:
            contour_area = cv.contourArea(c)
            if contour_area > 20:
                contour = GlobalEvent(c, contour_area)
                centroid_str = str(contour.center)
                if centroid_str in self.global_events:
                    self.global_events[centroid_str].update(contour_area, contour.max_rect)
                else:
                    new = True
                    for k, v in self.global_events.items():
                        if contour.isInPrevContour(v):
                            new = False
                            v.update(contour_area, contour.max_rect)
                            break
                    if new:
                        self.global_events[centroid_str] = contour

        to_discard = []
        now = time.time()
        replay = False
        for ge_k in self.global_events:
            ge: GlobalEvent = self.global_events[ge_k]
            last_updated = ge.updated
            # trail ended
            if now - last_updated > 0.1:
                to_discard.append(ge_k)

                # exclude trails that are too short or too long
                if 0.3 < last_updated - ge.st_t < 5:
                    # exclude stationary trails
                    if np.linalg.norm(ge.st_pos - ge.last_pos) > 5:
                        self.replay(self._buffer.getCopy(), ge.max_rect)
                        self.saveMeteor(self._buffer.getCopy(), frame_no)
                        replay = True
                        if frame_no:
                            print(f"{frame_no/20}s")
                        break

        for k in to_discard:
            del self.global_events[k]

        self.toLive(img)

    def saveMeteor(self, buf, frame_no):
        print("--------------saving--------------")
        pro = Process(target=saveMeteor, args=(buf, self._fps, frame_no))
        pro.daemon = True
        pro.start()

    def replay(self, buffer, roi_rect):
        # discard frames during cool down time
        max_ctr = buffer.maxlen - 10
        for i, obj in enumerate(buffer):
            img = obj['img']
            img = cv.cvtColor(img, cv.COLOR_BAYER_BG2BGR)
            rect = scale_rect(roi_rect, 3)
            x, y, w, h = rect
            cv.rectangle(img, (x, y), (x + w, y + h), (200, 127, 127), 1)
            cv.putText(img, 'Replay', (0, 50), 0, 2, (255, 255, 0), thickness=8)
            self.toLive(img)
            if i >= max_ctr:
                break
    
    def toLive(self, img: np.array):
        cv.imshow('frame', img)
        cv.waitKey(1)


def main():
    config = configparser.ConfigParser()
    config.read('settings.ini')

    processor = Processor(config)
    cap = cv.VideoCapture("/Users/siyu/Downloads/test.mov")

    ctr = 0

    while cap.isOpened():
        # print(ctr)
        ctr += 1
        ret, frame = cap.read()
        # cv.imshow('live', frame)
        # frame = cv.resize(frame, (1304, 976))
        frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        processor.process(frame, ctr)
        # print(ctr)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break


if __name__ == '__main__':
    main()
