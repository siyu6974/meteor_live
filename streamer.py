import queue
import threading
import cv2 as cv
import subprocess as sp
from PIL import ImageGrab
import numpy as np
import time


class Live(object):
    def __init__(self):
        self.frame_queue = queue.Queue()
        self.rtmpUrl = ""

        self.command = ['ffmpeg',
                        '-y',
                        '-f', 'rawvideo',
                        '-vcodec', 'rawvideo',
                        '-pix_fmt', 'bgr24',
                        '-s', "{}x{}".format(1920, 1080),
                        '-r', '24',  # fps
                        '-i', '-',

                        '-c:v', 'libx264',
                        '-b:v', '1500k',
                        '-pix_fmt', 'yuv420p',
                        '-preset', 'ultrafast',
                        # '-g', '20',

                        '-threads', '0',
                        '-bufsize', '1024k',
                        '-f', 'flv',
                        self.rtmpUrl]

    def push_frame(self):
        # 防止多线程时 command 未被设置
        while True:
            if len(self.command) > 0:
                # 管道配置
                p = sp.Popen(self.command, stdin=sp.PIPE)
                print(self.command)
                break

        f_str = ''
        # printscreen_pil = ImageGrab.grab()
        # frame = np.array(printscreen_pil, dtype='uint8')
        # f_str = frame.tostring()

        while True:
            img = np.random.random((1920, 1080, 3))
            p.stdin.write(img.tostring())
            # time.sleep(0.01)

            # if ctr <= 0:
            #     time.sleep(10)
            #     print('=================')
            #     continue
            # if self.frame_queue.empty() != True:
            #     frame = self.frame_queue.get()
            #     # process frame
            #     # 你处理图片的代码
            #     # write to pipe
            #     f_str = frame.tostring()
            #     p.stdin.write(f_str)
            # else:
            #     if len(f_str):
            #         p.stdin.write(f_str)
            # print(1)
            # time.sleep(0.05)

    def run(self):
        self.push_frame()
        # threads = [
        #     threading.Thread(target=Live.read_frame, args=(self,)),
        #     threading.Thread(target=Live.push_frame, args=(self,))
        # ]
        # [thread.setDaemon(True) for thread in threads]
        # [thread.start() for thread in threads]


live = Live()
live.run()
while True:
    time.sleep(1)
