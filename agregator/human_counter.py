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
from agregator.agregator import AgregatorBase
from common.settings import HUMAN_COUNTER_TAG


class AgregatorHumanCounter(AgregatorBase):
    def __init__(self, logger, config, detection_pipe_ends,
                 message_client, **kwargs):
        self.name = HUMAN_COUNTER_TAG
        self.agregate_module_name = 'agregator.agregator_base.counter'
        self.agregate_class_name = 'Counter'
        AgregatorBase.__init__(self, logger, config, detection_pipe_ends,
                               message_client, **kwargs)
