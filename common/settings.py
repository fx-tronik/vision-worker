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
DEBUG = True

LOGGER = {
    'default_name': 'BaseDaemon',
    'level': 'DEBUG',
    'save_path': 'log/vision_worker/{0}.txt',
    'file_size_mb': 10,
    'amount_backup_files': 2,
}

MOSQUITTO_CONNECT = {
    'host': '127.0.0.1',
    'port': 1885,
    'client_id': 'vision_worker'
}
MESSAGE_PREFIX = 'cv-ws'
PID_FILE_PATH = '/tmp'

#processors
HUMAN_POSE_TAG = 'human_pose_localizer'
PLATES_PROC_TAG = 'plates_localizer'

#agregators
HUMAN_COUNTER_TAG = 'zones_counter'
PLATES_AGR_TAG = 'ocr_agr'

CONFIGURATOR = {
        #'url': 'http://127.0.0.1:5000/config',
        'url': 'http://192.168.0.125:8080/api/cameras/',
        'local_file': 'configs/config.json',
        'save_backup': True
        }

STREAM_DISPATCHER = {
        'pid_prefix': 'StreamDispatcher'
        }

STREAM_PROCESSOR = {
        'pid_prefix': 'StreamProcessor'
        }

PROCESSOR = {
        'pid_prefix': 'Processor',
        'constraints': {
                HUMAN_POSE_TAG:{
                'image_size': (1280, 720)
                },
            }
        }

AGREGATOR = {
        'pid_prefix': 'Agregator',
        }
