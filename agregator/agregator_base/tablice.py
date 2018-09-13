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
from agregator.agregator_base.agregate_processor_base import AgregateProcessor
from time import time
import numpy as np
import cv2
from common.utils import search_in_dict_list


class TabliceAGR(AgregateProcessor):
    def __init__(self, config):
        self.config = config['config']
        self.last_detection = {}
        self.last_zones = {}
        self.last_sent = {}
        self.min_period = 5.

    def process(self, detection_with_meta):
        if detection_with_meta is None or not isinstance(detection_with_meta, tuple):
            return None
        meta, ocr = detection_with_meta
        width, height = meta['image_width'] , meta['image_height']
        detection, corners = ocr

        streamer_id = meta['streamer_id']
        if not (streamer_id in self.last_zones):
            self.last_zones[streamer_id] = {}
            self.last_sent[streamer_id] = time()
            self.last_detection[streamer_id] = {}
        zones_config = search_in_dict_list(self.config['cameras'], 'id', streamer_id)['zone_cameras']
        zones_plates = {}
        for zone in zones_config:
            if "agregator_zone" in zone:
                agregator_zone = zone["agregator_zone"]
                for _ in (agr for agr in agregator_zone if agr['agregator'] == 'ocr_agr'):
                    zones_plates[zone['id']] = []
                    detected_plates = []
                    double_detected = []

                    polygon = zone['polygons']
                    if len(polygon) >= 3:
                        #ATTENTION - ONLY ONE POLYGON FOR ZONE FOR NOW
                        contour = [None] * len(polygon)
                        for i, pt in enumerate(polygon):
                            contour[i] = (pt['x'], pt['y'])
                    else:
                        contour = [(0,0), (width,0), (width,height), (0,height)]
                    contour = np.expand_dims(contour, 1)

                    for plate, cor in zip(detection, corners):
                        if cv2.pointPolygonTest(contour, tuple(cor[0]), False) > 0:
                            detected_plates.append(plate)
                            if zone['id'] in self.last_detection[streamer_id]:
                                if plate in self.last_detection[streamer_id][zone['id']]:
                                    double_detected.append(plate)
                    zones_plates[zone['id']]=','.join(double_detected)
                    self.last_detection[streamer_id][zone['id']] = detected_plates

        message = None
        if zones_plates != self.last_zones[streamer_id] \
        or (time() - self.last_sent[streamer_id]) > self.min_period:
            message = zones_plates
            self.last_sent[streamer_id] = time()
        self.last_zones[streamer_id] = zones_plates

        return message
