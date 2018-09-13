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
class ConnectionFailure(Exception):
    def __init__(self, name, message):
        self.name = name
        self.message = message

    def __str__(self):
        return 'Connection failure [client: %s; message: %s]' % (
            self.name, self.message)


class ReconnectFailure(ConnectionFailure):
    def __init__(self, name, try_amount, message):
        super(ReconnectFailure, self).__init__(name, message)
        self.try_amount = try_amount

    def __str__(self):
        return 'Client %s can not connect after %i attempts' % (
            self.name, self.try_amount)

