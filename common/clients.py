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
import paho.mqtt.client as mqtt
from common.settings import MOSQUITTO_CONNECT
from common.exceptions import ConnectionFailure

class CustomMqttClient(mqtt.Client):
 
    def _handle_on_message(self, message):
        try:
            super(CustomMqttClient, self)._handle_on_message(message)
        except Exception as e:
            error = {"exception": str(e.__class__.__name__), "message": str(e)}

class Client(object):
    def __init__(self, logger, **kwargs):
        self.connection = None
        self.log = logger
        self.connect()
        
class ClientMosquitto(Client):
    def connect(self):
        # Avoid reconnect every time we call function.
        if self.connection is not None:
            return True
        client = CustomMqttClient(MOSQUITTO_CONNECT['client_id'])
        client.on_connect = self.on_connect
        client.on_disconnect = self.on_disconnect
        try:
            client.connect(MOSQUITTO_CONNECT['host'], MOSQUITTO_CONNECT['port'])
            self.connection = client
        except ConnectionRefusedError as error:
            raise ConnectionFailure('Mosquitto connection', error)
            
    def publish(self, topic, message):
        try:
            self.connection.publish(topic, message)
        except BrokenPipeError as error:
            raise ConnectionFailure('Mosquitto connection', error)
            
    def on_connect(self, client, userdata, flags, rc):
        self.log.info('Mosquitto: Connection opened')
    
    def on_disconnect(self, client, userdata, rc):
        self.log.info('Mosquitto: Connection closed')
        