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
from agregator.agregator_base.agregate_processor_base import AgregateProcessor
import cv2
import numpy as np
import json
from time import time
from common.utils import search_in_dict_list
#import matplotlib.pyplot as plt

class Counter(AgregateProcessor):
    def __init__(self, config):
        self.config = config['config']
        self.last_sent = time()
        self.min_period = 5.
        self.zones_past = {}

    def process(self, detection_with_meta):
        meta, detection = detection_with_meta
        return str(detection)

