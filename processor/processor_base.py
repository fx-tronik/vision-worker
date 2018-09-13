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
import os
os.environ["CUDA_VISIBLE_DEVICES"]='0'
import traceback
from importlib import import_module
from multiprocessing import Process, Value

class ProcessorBase:
    def __init__(self, logger, image_queues, pipe_starts, **kwargs):
        self.log = logger
        self.image_queues = image_queues
        self.pipe_starts = pipe_starts
        self.weights_path = self.get_weights()

        self.is_processor_running = Value('b', False)
        self.process_detect = Process(target=self.detect_process, args=(self.is_processor_running,))
        self.process_detect.start()
        #wait for network loading
        #self.is_processor_running = Value('b', True)

    def detect_process(self, condition):
        inference_module = import_module(self.inference_module_name)
        print(self.name)
        if self.name == 'human_pose_localizer':
            os.environ["CUDA_VISIBLE_DEVICES"]='1'
            print("karta 1")
        if self.name == 'plates_localizer':
            os.environ["CUDA_VISIBLE_DEVICES"]='1'
            print("karta 1")
        network_class = getattr(inference_module, self.inference_class_name)
        network = network_class(self.weights_path)
        condition.value = True
        while True:
            self.get_detections(network)

    def get_weights(self):
        #TODO weights can be downloaded from external server
        #local_file = os.path.join( os.path.expanduser('~/data'),
        #                          'models', self.weights_file)
        local_file = os.path.join( os.path.expanduser('~/workspace/SVS'),
                                  'models', self.weights_file)
        return local_file

    def get_detections(self, network):
        for queue_id, queue in enumerate(self.image_queues):
            image_with_meta = queue.get()
            if image_with_meta is None:
                self.log.warn('Processor get empty image from queue')
                continue
            meta, image = image_with_meta
            meta['model_name'] = self.name
            meta['image_height'], meta['image_width'] = image.shape[:2]
            try:
                detection = network.inference(image)
                for pipe in self.pipe_starts:
                    pipe.send((meta, detection))
            except Exception as error:
                self.log.critical(traceback.fotrmat_exc(error))
                for pipe in self.pipe_starts:
                    pipe.send(None)

    def loop(self):
        if self.process_detect.is_alive() is False:
            self.log.fatal("process_detect process is dead")
            raise Exception('process_detect process is dead.')
