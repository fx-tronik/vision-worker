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
from importlib import import_module
from multiprocessing import Process, Value
import traceback
from time import sleep
import json
from common.settings import MESSAGE_PREFIX


class AgregatorBase:
    def __init__(self, logger, config, detection_pipe_ends,
                 message_client, **kwargs):
        self.log = logger
        self.config = config
        self.detection_pipe_ends = detection_pipe_ends
        self.message_client = message_client
        self.is_agregator_running = Value('b', False)
        self.process_agregate = Process(target=self.agregate_process, args=(self.is_agregator_running,))
        self.process_agregate.start()
        self.retry_timeout = 10

    def agregate_process(self, condition):
        agregate_module = import_module(self.agregate_module_name)
        agreagte_class = getattr(agregate_module, self.agregate_class_name)
        agregator = agreagte_class({'config':self.config},)
        condition.value = True
        while True:
            self.agregate_detections(agregator)

    def agregate_detections(self, agregator):
        for pipe_end in self.detection_pipe_ends:
            detection_with_meta = pipe_end.recv()

            #Prowizoryczne formatowanie danych do wyslania
            try:
                to_send = None
                message = agregator.process(detection_with_meta)
                if message and type(message) is dict:
                    message_dict = message.copy()
                    for k, v in message_dict.items():
                        message_dict[k] = {self.name: message_dict[k]}
                    to_send = json.dumps(message_dict)

            except Exception as error:
                self.log.critical(traceback.fotrmat_exc(error))
                message = None
                to_send = None

            #WebSerwer przyjmuje dane w topicu "data"
            if message:
                self.log.info('Message: {} on topic = {}/{}'.format(to_send,
                              MESSAGE_PREFIX, 'data'))
            if string:
                self.message_client.publish(topic='{}/{}'.format(MESSAGE_PREFIX,
                                            'data'), message=to_send)

    def loop(self):
        if self.process_agregate.is_alive() is False:
            self.log.fatal("process_agregate process is dead")
            raise Exception('process_agregate process is dead.')
