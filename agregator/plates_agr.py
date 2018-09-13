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
from common.settings import PLATES_AGR_TAG


class AgregatorPlates(AgregatorBase):
    def __init__(self, logger, config, detection_pipe_ends,
                 message_client, **kwargs):
        self.name = PLATES_AGR_TAG
        self.agregate_module_name = 'agregator.agregator_base.tablice'
        self.agregate_class_name = 'TabliceAGR'
        AgregatorBase.__init__(self, logger, config, detection_pipe_ends,
                               message_client, **kwargs)
