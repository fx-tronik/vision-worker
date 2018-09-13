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
from os.path import normpath, join
from multiprocessing import Process
from common.settings import DEBUG, LOGGER, PID_FILE_PATH
from common.daemon import Daemon
from common.logger import Log
from common.clients import ClientMosquitto
from common.exceptions import ReconnectFailure

class Base(Daemon):
    transport_clients = {'Mosquitto': ClientMosquitto}

    def __init__(self,
                 logger_name='',
                 pid_file_name='',
                 database=None,
                 message_bus=None,
                 cache=None,
                 **kwargs):

        Daemon.__init__(self, self.pid_filepath(pid_file_name))

        if not logger_name:
            logger_name = LOGGER['default_name']
            
        self.subscribers = {}
            
        log_path = LOGGER['save_path'].format(pid_file_name)
        self.log = Log(logger_name,
               LOGGER['level'],
               DEBUG,
               log_path,
               LOGGER['file_size_mb'],
               LOGGER['amount_backup_files'])
        
        self.message_bus = self.init_client(message_bus, **kwargs)
        
    def initial(self, arguments=None, after_exit=True):
        self.log.info('Daemon initial')

        if DEBUG:
            self.notify('debug')
            self.run()
            sys.exit(0)

        if not arguments:
            arguments = sys.argv

        if len(arguments) >= 2:
            if 'start' == arguments[1]:
                self.start()
                self.log.info('Daemon started')
                self.notify('start', sys.argv)
            elif 'stop' == arguments[1]:
                self.stop()
                self.log.info('Daemon stopped')
                self.notify('stop', arguments)
            elif 'restart' == arguments[1]:
                self.restart()
                self.log.info('Daemon restarted')
                self.notify('restart', arguments)
            else:
                print('Unknown command')
                self.log.warning('Daemon command not allowed')
                self.notify('unknown', arguments)
                sys.exit(2)

            if after_exit:
                sys.exit(0)
        else:
            self.log.warning('Daemon command not found (Usage: start|stop|restart)')
            print('Usage: %s start|stop|restart' % arguments[0])
            sys.exit(2)   
            
    def notify(self, name, *args, **kwargs):
        try:
            if name in self.subscribers:
                for subscriber_callback in self.subscribers[name]:
                    self.log.debug('Send notification "%s"' % name)
                    subscriber_callback(*args, **kwargs)
        except ReconnectFailure as error:
            self.log.critical(error.__str__())
            sys.exit(4)
        except KeyError as ignore:
            self.log.error('Key %s not found' % ignore.message)
        except Exception as error:
            self.log.critical('Notify worker error: (%s)' % error)
            sys.exit(4)

    def subscribe(self, name, callback):
        if name not in self.subscribers:
            self.subscribers[name] = []

        self.subscribers[name].append(callback)
        self.log.debug('Subscriber "%s" success added with callback "%s"' %
                       (name, callback.__name__))
        
    def init_client(self, client_name, **kwargs):
        if client_name is None:
            return None
        try:
            return self.transport_clients[client_name](self.log, **kwargs)
        except KeyError:
            raise Exception('Client "%s" not found' % client_name)
            
    def run(self):
        try:
            self.log.debug('Daemon worker started')
            while True:
                self.notify('iteration')
        except Exception as error:
            self.log.critical('Worker error: (%s)' % error.message)
            sys.exit(4)
            
    def pid_filepath(self, filename):
        return normpath(join(PID_FILE_PATH, filename + '.txt'))
            
class BaseWorker(Base):
    def __init__(self, pid_prefix, module, **kwargs):
        Base.__init__(self,
                      pid_file_name='{}.{}'.format(pid_prefix, module),
                      **kwargs) 
        
class BaseProcess(Base):
    def __init__(self, prefix, module='BaseProcess', **kwargs):
        Base.__init__(self,
                      logger_name=prefix,
                      pid_file_name='{}.{}'.format(prefix, module),
                      **kwargs)
        self.prefix = prefix
        self.module_name = module
        self.all_process = {}

    def initial_start(self):
        if self.is_running():
            self.log.warning('%s:%s already started' % (self.prefix, self.module_name))
            sys.exit(1)
        self.initial_start_callback()

    def initial_stop(self):
        if DEBUG and not self.is_running():
            print('%s:%s not running' % (self.prefix, self.module_name))  
            sys.exit(1)
        self.initial_stop_callback()

    def initial_restart(self):
        self.initial_stop()
        self.initial_start()
        self.log.info('%s:%s restarted' % self.prefix, self.module_name)

    def is_started(self, process):
        if process.is_alive():
            self.log.info('From "%s" running module "%s"' % (self.prefix, self.module_name))
            return True

        self.log.warning('From "%s" not running module "%s"' % (self.prefix, self.module_name))
        return False

    def start_process(self, name, **kwargs):
        process = Process(name=name,
                          target=self.process_callback,
                          kwargs=kwargs)
        process.start()

        if DEBUG:
            self.all_process[name] = process

        return process

    def stop_process(self, name):
        self.log.info('Stopped process "%s"' % name)
        self.pidfile = self.pid_filepath(self.prefix + '.' + name)

        if not DEBUG:
            self.initial(['', 'stop'], after_exit=False)
        else:
            del self.all_process[name]

    def is_running(self):
        return len(self.all_process) > 0

    def process_callback(self, **kwargs):
        pass

    def initial_start_callback(self):
        pass

    def initial_stop_callback(self):
        pass


class MapperBaseProcess(BaseProcess):
    """
    Maps a listener to a new subprocess
    """

    def __init__(self, prefix, module_name, callback_daemon, **kwargs):
        BaseProcess.__init__(self, prefix)
        self.listener_callback = callback_daemon
        self.module_name = module_name
        self.args = kwargs

    def initial_start_callback(self):
        process = self.start_process(name=self.module_name, **self.args)
        self.is_started(process)

    def initial_stop_callback(self):
        self.stop_process(self.module_name)

    def process_callback(self, **kwargs):
        daemon = self.listener_callback(self.prefix, self.module_name, **kwargs)
        daemon.initial(['', 'start'])