from multiprocessing import Queue, Process
import cv2 as cv
import subprocess as sp
import numpy as np
import time
from utils import FPS


class Streamer(object):
    def __init__(self, conf):
        self.frame_queue = Queue(maxsize=90)
        self.rtmpUrl = f"{conf['stream']['adr']}{conf['stream']['key']}"

        self.command = ['ffmpeg',
                        '-y',

                        '-f', 'rawvideo',
                        '-vcodec', 'rawvideo',
                        '-pix_fmt', 'bgr24',
                        '-s', f"{conf['capture']['size_w']}x{conf['capture']['size_h']}",
                        '-r', str(1 / float(conf['capture']['exposure'])),
                        '-i', '-',

                        '-c:v', 'libx264',
                        '-b:v', '1500k',
                        '-pix_fmt', 'yuv420p',
                        '-preset', 'ultrafast',
                        '-g', '20',
                        '-threads', '0',
                        '-bufsize', '1024k',
                        '-f', 'flv',
                        self.rtmpUrl]
        # TODO:
        # self.p = sp.Popen(self.command, stdin=sp.PIPE)
        self.fps = FPS()

    def push_frame(self, frame: np.array):
        self.frame_queue.put(frame)

    def _encoder(self):
        while True:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                cv.imshow('live', frame)
                cv.waitKey(1)
                self.fps.count()
                print(self.fps.read())
                # TODO:
                # self.p.stdin.write(frame.tostring())
            else:
                time.sleep(0.01)

    def run(self):
        th = Process(target=Streamer._encoder, args=(self, ))
        th.daemon = True
        th.start()

