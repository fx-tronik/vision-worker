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
from streamer.streamer import StreamerBase


class Camera(StreamerBase):
    def __init__(self, logger, streamer_config, image_queue, **kwargs):
        StreamerBase.__init__(self, logger, streamer_config, image_queue, **kwargs)
