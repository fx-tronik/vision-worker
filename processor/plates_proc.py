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
from processor.processor_base import ProcessorBase
from common.settings import PLATES_PROC_TAG

class PlatesLocalizer(ProcessorBase):
    def __init__(self, logger, image_queues, pipe_starts,  **kwargs):
        self.name = PLATES_PROC_TAG
        self.inference_module_name = 'processor.detector_base.plates.plates_ocr'
        self.inference_class_name = 'PlatesOCR'
        self.weights_file = ''
        ProcessorBase.__init__(self, logger, image_queues, pipe_starts,  **kwargs)
