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
from time import sleep
from common.base import BaseWorker
from processors_helper import PROCESSORS, AGREGATORS
from streamer.camera import Camera
from multiprocessing import Process, Value, Queue, Pipe
import traceback

class Processor(BaseWorker):
    def __init__(self, pid_prefix, module, config_name, config):
        BaseWorker.__init__(self, pid_prefix, module,
                            message_bus='Mosquitto',
                            logger_name='Processor')

        self.config_name = config_name
        self.config = config
        self.pipes, self.processors, self.agregators = self.parse_config(config)
        self.stream_buffers = []
        self.stream_meta = []
        self.detection_buffers = []
        self.detection_meta = []
        self.message_client = self.init_client('Mosquitto')


        self.launched_streamer_processes, self.are_streamers_ok = self.init_streamer()
        self.launched_processing_processes, self.are_processors_ok = self.init_processor()
        self.launched_agregating_processes, self.are_agregators_ok = self.init_agregator()

        self.subscribe('iteration', self.iteration)

    def parse_config(self, config):
        cameras_config = config['cameras']
        agregators = {}
        processors = {}
        for camera_config in cameras_config:
            camera_id = camera_config['id']
            for zone in camera_config['zone_cameras']:
                for goal in zone['agregator_zone']:
                    # wybor procesora na podstawie agregatora -
                    # czy goal['type'] jest rzeczywiscie potrzebne?
                    agregator = goal['agregator']
                    if agregator == 'ocr_agr':
                        processor = 'plates_localizer'
                    if agregator == 'zones_counter':
                        processor = 'human_pose_localizer'
                    processors.setdefault(processor, []).append(camera_id)
                    agregators.setdefault(agregator, []).append(processor)
        pipes = {}
        for agregator_name, agr_processors in agregators.items():
            for processor_name in list(set(agr_processors)):
                p_output, p_input = Pipe()
                pipes.setdefault(agregator_name, []).append(p_output)
                pipes.setdefault(processor_name, []).append(p_input)
        return pipes, processors, agregators

    def check_subprocesses(self):
        #CHECK STREAMERS
        not_alive_streamers = []
        for process_id, process in enumerate(self.launched_streamer_processes):
            if process.is_alive() is False:
                not_alive_streamers.append(process_id)

        #CHECK PROCESSORS
        not_alive_processors = []
        for process_id, process in enumerate(self.launched_processing_processes):
            if process.is_alive() is False:
                not_alive_processors.append(process_id)

        #CHECK AGGREGATORS
        not_alive_agregators = []
        for process_id, process in enumerate(self.launched_agregating_processes):
            if process.is_alive() is False:
                not_alive_agregators.append(process_id)

        if len(not_alive_streamers) > 0:
            self.terminate_subprocesses()
            self.log.warn("One or more streamer processes is not alive. Dead workers: {}".format(not_alive_streamers))
        if len(not_alive_processors) > 0:
            self.terminate_subprocesses()
            raise Exception("One or more processing processes is not alive. Dead workers: {}".format(not_alive_processors))
        if len(not_alive_agregators) > 0:
            self.terminate_subprocesses()
            raise Exception("One or more agregating processes is not alive. Dead workers: {}".format(not_alive_agregators))

    def terminate_subprocesses(self):
        for p in self.launched_streamer_processes:
            if p.is_alive():
                p.terminate()
        for p in self.launched_processing_processes:
            if p.is_alive():
                p.terminate()
        for p in self.launched_agregating_processes:
            if p.is_alive():
                p.terminate()
        self.stop()

    def iteration(self):
        self.check_subprocesses()
# =============================================================================
#         self.log.debug('Buffer will be tested')
#         self.test_buffers()
#         self.log.debug('Buffer was tested')
# =============================================================================
        sleep(5)

    def init_processor(self):
        launched_processing_processes = []
        are_processors_ok = []
        for processor_type, stream_ids in self.processors.items():
            self.log.debug('Launching processing process {}'.format(processor_type))
            queue_cnts = [i for i in range(len(self.stream_buffers)) if self.stream_meta[i]['id'] in stream_ids]
            buffer_queues = [self.stream_buffers[i] for i in queue_cnts]
            buffer_metas = [self.stream_meta[i] for i in queue_cnts]
            self.detection_meta.append({'ids': [meta['id'] for meta in buffer_metas]})
            processor_ok = Value('b', True)
            pipe_starts = self.pipes[processor_type]
            self.log.debug('Processor will be defined')
            process = Process(target=self.launch_instance, args=(PROCESSORS[processor_type]['callback'],),
                kwargs=(
                {
                    'logger': self.log,
                    'image_queues': buffer_queues,
                    'pipe_starts': pipe_starts,
                    'is_process_ok': processor_ok
                }))
            self.log.debug('Processor will be started')
            process.start()
            self.log.debug('Processor is started')
            are_processors_ok.append(processor_ok)
            launched_processing_processes.append(process)
        return launched_processing_processes, are_processors_ok

    def init_dispatcher(self):
        pass

    def init_agregator(self):
        launched_agregating_processes = []
        are_agregators_ok = []
        agregators = {}
        for agregator_type, processors_names in self.agregators.items():
            self.log.debug('Launching agregating process {}'.format(agregator_type))
            agregator_ok = Value('b', True)
            pipe_ends = self.pipes[agregator_type]
            process = Process(target=self.launch_instance, args=(AGREGATORS[agregator_type]['callback'],),
                kwargs=(
                {
                    'logger': self.log,
                    'config': self.config,
                    'detection_pipe_ends': pipe_ends,
                    'message_client': self.message_client,
                    'is_process_ok': agregator_ok
                }))
            process.start()
            are_agregators_ok.append(agregator_ok)
            launched_agregating_processes.append(process)
        return launched_agregating_processes, are_agregators_ok



    def init_streamer(self):
        launched_streamer_processes = []
        are_streamers_ok = []
        for config_id, streamer_config in enumerate(self.config['cameras']):
            self.log.debug('Launching streamer process {} ({})'.format(config_id,
                           streamer_config.get('name', '')))
            buffer = Queue(1)
            self.stream_buffers.append(buffer)
            self.stream_meta.append({'id': streamer_config['id']})
            streamer_ok = Value('b', True)
            process = Process(target=self.launch_instance, args=(Camera,),
                              kwargs=({'logger': self.log,
                                       'image_queue': buffer,
                                       'streamer_config': streamer_config,
                                       'config_id': config_id,
                                       'is_process_ok': streamer_ok
                                      }))
            process.start()
            are_streamers_ok.append(streamer_ok)
            launched_streamer_processes.append(process)
        return launched_streamer_processes, are_streamers_ok

    def launch_instance(self, class_to_be_launched, **kwargs):
        is_process_ok = kwargs.pop('is_process_ok')
        instance_obj = class_to_be_launched(**kwargs)
        while True:
            try:
                instance_obj.loop()
            except Exception as ex:
                self.log.critical(traceback.format_exc(ex))
                is_process_ok.value = False


    #DEBUG FUNCTIONS
    def test_buffers(self):
        import cv2
        self.log.debug('Buffers number: {}'.format(len(self.stream_buffers)))
        for buffer in self.stream_buffers:
            self.log.debug(buffer.qsize())
            image = buffer.get()
            self.log.debug(image.shape)
            cv2.imshow('test', image)
            cv2.waitKey(2000)
        cv2.destroyAllWindows()
