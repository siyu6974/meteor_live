from multiprocessing import Queue, Process
import cv2 as cv
import subprocess as sp
import numpy as np
import time
from utils import FPS
from queue import Full


class Streamer(object):
    def __init__(self, conf):
        self.frame_queue = Queue(maxsize=90)
        self.rtmpUrl = f"{conf['stream']['adr']}{conf['stream']['key']}"

        self.audio = conf['stream']['music']

        self.command = ['ffmpeg',
                        '-y',

                        '-i', self.audio,

                        '-f', 'rawvideo',
                        '-vcodec', 'rawvideo',
                        '-pix_fmt', 'bgr24',
                        '-s', f"{conf['capture']['size_w']}x{conf['capture']['size_h']}",
                        '-r', str(1 / float(conf['capture']['exposure'])),
                        '-i', '-',

                        '-c:a', 'copy',
                        '-c:v', 'libx264',
                        '-b:v', '1500k',
                        '-pix_fmt', 'yuv420p',
                        '-preset', 'ultrafast',
                        '-g', '20',
                        '-threads', '0',
                        '-bufsize', '1024k',
                        '-f', 'flv',
                        self.rtmpUrl]

        self.p = sp.Popen(self.command, stdin=sp.PIPE)
        # self.fps = FPS()

    def push_frame(self, frame: np.array):
        try:
            self.frame_queue.put_nowait(frame)
        except Full:
            # discard old ones to make room for the current frame
            self.frame_queue.get()
            self.frame_queue.get()
            self.frame_queue.put(frame)

    def _encoder(self):
        while True:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                # cv.imshow('live', frame)
                # cv.waitKey(1)
                # self.fps.count()
                # print(self.fps.read())
                self.p.stdin.write(frame.tostring())
            else:
                time.sleep(0.01)

    def run(self):
        th = Process(target=self._encoder, args=())
        th.daemon = True
        th.start()

