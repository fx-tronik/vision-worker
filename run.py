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

import sys
from processor_daemon import Processor
from common.base import MapperBaseProcess
from common.logger import Log
from common.settings import LOGGER, DEBUG, STREAM_DISPATCHER
from common.configurator import Configurator


if __name__ == '__main__':

    logger = Log('run_script',
                 LOGGER['level'],
                 DEBUG,
                 LOGGER['save_path'],
                 LOGGER['file_size_mb'],
                 LOGGER['amount_backup_files'])
    if len(sys.argv) < 2:
        print('Fatal error. Action name must be provided \n Usage run start|stop|restart')
    action = sys.argv[1]
    prefix = STREAM_DISPATCHER['pid_prefix']
    configurator = Configurator()
    config = configurator.get_config()
    config_name = config['name']
    name = '{}_worker{}'.format(config_name, 0)
    obj = MapperBaseProcess(prefix, name, Processor, 
                            config_name=config_name,
                            config = config)        
    if 'start' == action:
        obj.initial_start()
    elif 'stop' == action:
        obj.initial_stop()
    elif 'restart' == action:
        obj.initial_restart()
    else:
        print("Unkown action")
        exit(-1)

