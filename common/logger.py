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

import sys, os
import logging
import logging.handlers



class Log(logging.Logger):
    levels = ['CRITICAL', 'DEBUG', 'ERROR', 'INFO', 'WARNING']

    def __init__(self, name, level, duplex, path, size_mb, backups=2):
        super(Log, self).__init__(name)

        dir_path = os.path.dirname(path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        handler = logging.handlers.RotatingFileHandler(path,
                                                       maxBytes=size_mb * 1024 * 1024,
                                                       backupCount=backups)

        formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')

        if duplex:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.addHandler(console_handler)

        handler.setFormatter(formatter)
        self.addHandler(handler)

        level = level.upper()

        if level not in self.levels:
            level = 'DEBUG'

        self.setLevel(level)
