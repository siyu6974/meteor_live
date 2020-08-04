import queue
import threading
import cv2 as cv
import subprocess as sp
import numpy as np
import time


class Streamer(object):
    def __init__(self, conf):
        self.frame_queue = queue.Queue(maxsize=30)
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

        self.p = sp.Popen(self.command, stdin=sp.PIPE)

    def push_frame(self, frame: np.array):
        try:
            frame = cv.cvtColor(frame, cv.COLOR_BAYER_BG2BGR)
            self.frame_queue.put(frame)
        except queue.Full:
            self.frame_queue.get_nowait()
            self.frame_queue.put_nowait(frame)

    def _encoder(self):
        while True:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                self.p.stdin.write(frame.tostring())
            else:
                time.sleep(0.1)

    def run(self):
        th = threading.Thread(target=Streamer._encoder, args=(self, ))
        th.setDaemon(True)
        th.start()

