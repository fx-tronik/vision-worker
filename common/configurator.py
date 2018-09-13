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
import requests
import json
import datetime
import shutil
import os
import numpy as np
from common.settings import CONFIGURATOR, LOGGER, DEBUG
from common.logger import Log
from common.exceptions import ConnectionFailure
class Configurator:
    def __init__(self):
        self.log = Log('configurator',
             LOGGER['level'],
             DEBUG,
             LOGGER['save_path'],
             LOGGER['file_size_mb'],
             LOGGER['amount_backup_files'])
        self.url = CONFIGURATOR['url']
        self.SAVE_BACKUP = CONFIGURATOR['save_backup']
        self.local_file = os.path.join(os.getcwd(),CONFIGURATOR['local_file'])
        self.config = None
        self.load()


    def load_from_web(self):
        config = None
        try:
            r = requests.get(self.url)
            config = r.json()
        except BaseException as error:
            raise ConnectionFailure('Config Web Loader', error)
        full_config = {}
        full_config['cameras'] = config
        full_config['name'] = 'FX_SVS'
        self.config = full_config

    def load_from_file(self):
        with open(self.local_file, 'r') as f:
            self.config = json.load(f)

    def load(self):
        try:
            self.load_from_web()
        except ConnectionFailure as error:
            self.log.warn('Web server is not responding; Loading config from file')
            self.load_from_file()
        if not self.verify():
            backup_dir = os.path.join(os.path.dirname(self.local_file),'backup')
            backup_file = os.path.join(backup_dir, sorted(os.listdir(backup_dir))[0])
            with open(backup_file, 'r') as f:
                self.config = json.load(f)
            self.log.warn('Config incomplete, last backup used')
        else:
            self.save_config()


    def save_config(self):
        if os.path.exists(self.local_file) and self.SAVE_BACKUP:
            backup_file = os.path.join(os.path.dirname(self.local_file),
                                       'backup',
                                       datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'.json')
            shutil.copy(self.local_file, backup_file)
            self.log.info('Backup config saved')
        with open(self.local_file, 'w') as f:
            json.dump(self.config, f)

    def check_fields(self, dictionary, required_fields):
        error = False
        errors = [field not in dictionary.keys() for field in required_fields]
        if np.any(errors):
            error = True
            self.log.error('Config incomplete, not contain required {} field'.format(required_fields[np.where(errors)[0][0]]))
        return error

    def verify(self):
        config = self.config

        required_fields = ['cameras', 'name']
        error = False
        error = self.check_fields(config, required_fields)

        camera_fields = ['id', 'formatted_url',
                         'zones', 'name']
        for camera in config['cameras']:
            error = self.check_fields(camera, camera_fields)

        return not error

    def get_config(self):
        return self.config


if __name__ == '__main__':
    configurator = Configurator()
    #configurator.load()
