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
from abc import ABC, abstractmethod


class AgregateProcessor(ABC):
    @abstractmethod
    def __init__(self, config):
        pass

    @abstractmethod
    def process(detections_with_meta):
        pass
