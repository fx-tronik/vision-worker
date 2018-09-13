#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
 _______  __   __  _______
|       ||  | |  ||       |
|  _____||  |_|  ||  _____|
| |_____ |       || |_____
|_____  ||       ||_____  |
 _____| | |     |  _____| |
|_______|  |___|  |_______|
'''
from multiprocessing import Process, Value
from time import sleep
import cv2
import datetime
import uuid

class StreamerBase:
    def __init__(self, logger, streamer_config, image_queue, **kwargs):
        self.retry_timeout = 10
        self.log = logger
        self.image_queue = image_queue
        self.streamer_config = streamer_config
        self.is_streamer_running = Value('b', False)
        self.process_buffer = Process(target=self.buffer_process, args=(self.is_streamer_running,))
        self.process_buffer.start()
        self.is_streamer_running = Value('b', True)

    def connect(self):
        self.log.debug('Connecting to streamer {}'.format(self.streamer_config['name']))
        cap = cv2.VideoCapture(self.streamer_config['formatted_url'])
        while not cap.isOpened():
            self.log.warn('Cannot connect to camera {}'.format(self.streamer_config['name']))
            sleep(self.retry_timeout)
            cap.open(self.streamer_config['formatted_url'])
        return cap

    def buffer_process(self, condition):
        cap = self.connect()
        while True:
            ret, frame = cap.read()
            if ret:
                while not self.image_queue.empty(): #flush last image
                    try:
                        self.image_queue.get_nowait()
                    except:
                        continue
                meta = self.generate_meta()
                self.image_queue.put((meta, frame))
            else:
                self.log.warn('Cannot grab frame from {}'.format(self.streamer_config['name']))
                cap = self.connect()

    def generate_meta(self):
        meta = {}
        meta['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        meta['id'] = str(uuid.uuid4())
        meta['streamer_id'] = self.streamer_config['id']
        return meta

    def loop(self):
        if self.process_buffer.is_alive() is False:
            self.log.warn("process_buffer of camera {} is dead".format(self.streamer_config['name']))
            sleep(5)
