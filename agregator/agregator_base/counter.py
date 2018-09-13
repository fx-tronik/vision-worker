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
import cv2
import numpy as np
import json
from time import time
from common.utils import search_in_dict_list
#import matplotlib.pyplot as plt

class Counter(AgregateProcessor):
    def __init__(self, config):
        self.config = config['config']
        self.last_sent = time()
        self.min_period = 5.
        self.zones_past = {}

    def process(self, detection_with_meta):
        if detection_with_meta is None or \
            not isinstance(detection_with_meta, tuple):
            return None
        meta, detection = detection_with_meta
        w, h = meta['image_width'] , meta['image_height']
        streamer_id = meta['streamer_id']
        zones_config = search_in_dict_list(self.config['cameras'], 'id', streamer_id)['zone_cameras'] # Zmiana nazewnictwa
        cnts = self.zones_to_cnts(zones_config, w, h)
        zones_with_humans = self.count(detection, cnts, w, h)
        message = None
        if self.change_in_directory(self.zones_past, zones_with_humans):
            message = self.make_message(zones_with_humans)
            self.zones_past.update(zones_with_humans)
        elif (time() - self.last_sent) > self.min_period:
            message = self.make_message(self.zones_past)
            self.last_sent = time()
        return message


    #Zmiana w okreslaniu konturow stref, ze wzgledu na inny format danych,
    #Rozpatrywanie tylko okreslonych stref, a nie wszystkich z danej kamery
    def zones_to_cnts(self, zones_config, width, height):
#        a = np.zeros((480, 640), dtype = np.uint8)
#        test_point1 = (500, 300)
        contours = {}
        for zone in zones_config:
            if "agregator_zone" in zone:
                  agregator_zone = zone["agregator_zone"]
                  for _ in (agr for agr in agregator_zone if agr["agregator"] == "zones_counter"):
                        polygon = zone['polygons']
                        if len(polygon) >= 3:
                              #ATTENTION - ONLY ONE POLYGON FOR ZONE FOR NOW
                              contour = [None] * len(polygon)
                              for i, pt in enumerate(polygon):
                                  contour[i] = (pt['x'], pt['y'])
                        else:
                              contour = [(0,0), (width,0), (width,height), (0,height)]
                        contour = np.expand_dims(contour, 1)
                        contours[zone['id']] = contour
                        #aa = cv2.drawContours(a, [contour], 0, (255), 3)
                        #plt.imshow(aa)
                        #print(cv2.pointPolygonTest(contour, test_point1, False))
                        break
        return contours

    def get_contact_point(self, human):
        #get position of human feet,
        #if not detected use shoulder and hip position to estimate
        contact_point = None
        #define key parts ids
        LShoulder = 5
        RShoulder = 2
        LHip = 11
        RHip = 8
        LAnkle = 13
        RAnkle = 10
        bps = human.body_parts
        feets = [LAnkle, RAnkle]
        shoulders = [LShoulder, RShoulder]
        hips = [LHip, RHip]
        leftSide = [LShoulder, LHip, LAnkle]
        rightSide = [RShoulder, RHip, RAnkle]
        #check if feet detected
        if all([feet in bps for feet in feets]): #feet are detected
            contact_point = (np.mean([bps[LAnkle].x, bps[RAnkle].x]),
                             np.mean([bps[LAnkle].y, bps[RAnkle].y]))

        elif all([part in bps for part in shoulders + hips]): #shoulders and hips detected
            hips_x = np.mean([bps[LHip].x, bps[RHip].x])
            hips_y = np.mean([bps[LHip].y, bps[RHip].y])
            shoulders_y = np.mean([bps[LShoulder].y, bps[RShoulder].y])

            contact_point = (hips_x, hips_y + 1.65*(hips_y - shoulders_y))

        elif all([part in bps for part in leftSide]): #left side visible
            contact_point = (bps[LAnkle].x, bps[LAnkle].y)

        elif all([part in bps for part in rightSide]): #right side visible
            contact_point = (bps[RAnkle].x, bps[RAnkle].y)

        return contact_point

    def present_in_contour(self, human, contour, w, h):
        contact_point = self.get_contact_point(human)
        if not contact_point:
            return None
        cpx = int(w * contact_point[0]+0.5)
        cpy = int(h * contact_point[1]+0.5)
        contact_point = (cpx, cpy)
        contour = contour.astype(np.int32)
        return cv2.pointPolygonTest(contour, contact_point, False) > 0

    def count(self, humans, contours, w, h):
        #zones = [{'id':cnt_id, 'human-silhouettes-no':0} for cnt_id in contours.keys()]
        zones = {}
        for zone_id, contour in contours.items():
            humans_no = 0
            for human in humans:
                if self.present_in_contour(human, contour, w, h):
                    humans_no += 1
            #zone = {'id':zone_id, 'human-silhouettes-no':humans_no}
            zones[zone_id] = humans_no
        return zones

    def change_in_directory(self, zones_past, zones_current):
        x = zones_past
        y = zones_current
        shared_items = {k: x[k] for k in x if k in y and x[k] == y[k]}
        return len(shared_items) < len(zones_current)

    def make_message(self, zones):
        message_dict = zones
        message_txt = json.dumps(message_dict)
        return message_dict
