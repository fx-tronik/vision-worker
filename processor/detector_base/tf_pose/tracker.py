#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  6 09:59:55 2018

@author: jakub
"""
from tf_pose.estimator import Human
from tf_pose.common import CocoPairs
import cv2
import numpy as np
import time
import matplotlib.pyplot as plt
import hashlib
import logging
import copy

logger = logging.getLogger('Tracker')
logger.setLevel(logging.DEBUG)

class GroupTracker:
    #manage tracking of many peoples
    def __init__(self, use_whole_human_tracking = True):
        self.trackers = {}
        self.humans = {}
        self.tracker_type = 'MOSSE'
        #when tracker failed to re-initialize on 'attempts to kill' frames, it will be killed
        self.attempts_to_kill = 2
        self.use_whole_human_tracking = use_whole_human_tracking
    def init(self, humans, frame):
        new_hids = []
        for human in humans:
            human_tracker = HumanTracker(tracker_type = self.tracker_type,
                                         use_whole_human_tracking=self.use_whole_human_tracking)
            part_trackers = human_tracker.init(human, frame)
            if part_trackers < 4:
                continue
            hid = human_tracker.set_hid()
            self.trackers[hid] = human_tracker
            self.humans[hid] = human
            new_hids.append(hid)
        return new_hids

    def update(self, frame):
        #update human pose based on trackers only
        #vis_frame = np.copy(frame)
        for hid, human_tracker in self.trackers.items():
            human_tracker.update(frame)
            self.humans[hid] = human_tracker.get_human()
            #vis_frame = human_tracker.draw_bboxes(vis_frame)
            #vis_frame = human_tracker.draw_id(vis_frame)


    def reinit(self, nn_humans, frame):
        #update trackers with human pose based on neural localizator
        humans = copy.deepcopy(nn_humans)
        new_hids, current_hids, removed_hids = [], [], []
        trackers_to_remove = []
        logger.debug('Reinit, {} humans'.format(len(humans)))
        for hid, human_tracker in self.trackers.items():
            logger.debug('Tracker {}'.format(hid))
            human_iter = human_tracker.reinit(humans, frame)
            logger.debug('Found iter: {}'.format(human_iter))
            current_hids.append(hid)
            if human_iter is not None: #tracker re-initialized i human_iter-th human in list
                del humans[human_iter]
                logger.debug('Humans left: {}'.format(len(humans)))
            else: #matching human is not found, kill tracker?
                attempts = human_tracker.get_attempts()
                logger.debug('Human {} not matched, attemp: {}'.format(hid, attempts))
                if attempts >= self.attempts_to_kill:
                    human_tracker.kill()
                    logger.debug('Human {} will be killed'.format(hid))
                    trackers_to_remove.append(hid)
                    del current_hids[-1]
        for hid in trackers_to_remove:
            logger.debug('Tracker removing {}'.format(hid))
            removed_hids.append(hid)
            del self.humans[hid]
            del self.trackers[hid]
        #what if peoples left?
        for human in humans:
            #create new trakcker:
            logger.debug('Create new human')
            human_tracker = HumanTracker(tracker_type = self.tracker_type,
                                         use_whole_human_tracking=True)
            part_trackers = human_tracker.init(human, frame)
            if part_trackers < 4:
                continue
            hid = human_tracker.set_hid()
            self.trackers[hid] = human_tracker
            self.humans[hid] = human
            logger.debug('Initialized human {}!'.format(hid))
            new_hids.append(hid)
        return new_hids, current_hids, removed_hids

    def draw_boxes(self, frame):
        vis_frame = np.copy(frame)
        for hid, human_tracker in self.trackers.items():
            #vis_frame = human_tracker.draw_bboxes(vis_frame)
            vis_frame = human_tracker.draw_id(vis_frame)
            vis_frame = human_tracker.draw_human_bbox(vis_frame)
        return vis_frame

    def get_humans(self):
        return list(self.humans.values())

class HumanTracker:
    def __init__(self, tracker_type = None, use_whole_human_tracking = False):
        if not tracker_type:
            self.tracker_type = 'MOSSE'
        else:
            self.tracker_type = tracker_type
        self.attempts = 0 #number of failed attempts of match human to tracker
        self.color = np.random.randint(128, 255, 3)
        self.use_whole_human_tracking = use_whole_human_tracking

    def init(self, human, frame):
        #init trackers for body part with human
        h, w, _ = frame.shape
        self.set_wh(w, h)
        self.human = human
        bbxs = self.get_bboxes()
        trackers = {}
        for pid, bbox in bbxs.items():
            new_tracker = self._create_single_tracker(bbox)
            new_tracker.init(frame,tuple(bbox))
            trackers[pid] = new_tracker
        if self.use_whole_human_tracking:
            human_bbx = self._whole_human_bb()
            if human_bbx is not None:
                human_tracker = self._create_single_tracker(human_bbx)
                human_tracker.init(frame, tuple(human_bbx))
                self.human_tracker = human_tracker
                self.human_bb = human_bbx
        self.trackers = trackers
        return len(self.trackers)

    def find_matching_human(self, humans):
        #find human with minimum distance
        distances = {}
        for i, other_human in enumerate(humans):
            distances[i] = self.get_distance(other_human)

        #return list(distances.keys())[np.argmin(distances.values())]
        print('Distances {}'.format(distances))
        match = np.argmin(list(distances.values()))
        min_dist = np.min(list(distances.values()))
        if self._get_base_dim() is None:
            return -1
        k = 2
        thr = k * self._get_base_dim() * 17
        if min_dist < thr:
            print('MIN DIST: {}, threshold: {}, return: '.format(min_dist, thr), list(distances.keys())[match])
            return list(distances.keys())[match]
        else:
            #print('NO MATCH: MIN DIST: {}, threshold: {}'.format(min_dist, self._get_base_dim() * 17))
            return -1

    def reinit(self, humans, frame):
        #update trackers with new joint poses
        if not humans:
            return None
        best_match  = self.find_matching_human(humans)
        if best_match == -1:
            logger.debug('Human has not match')
            self.attempts += 1
            return None
        new_human = humans[best_match]
        self.human = new_human
        bbxs = self.get_bboxes()
        for pid, bbox in bbxs.items():
            if pid in self.trackers.keys():
                self.trackers[pid].init(frame, tuple(bbox))
            else:
                self.trackers[pid] = self._create_single_tracker(bbox)
        if self.use_whole_human_tracking:
            human_bbx = self._whole_human_bb()
            if human_bbx is not None:
                human_tracker = self._create_single_tracker(human_bbx)
                human_tracker.init(frame, tuple(human_bbx))
                self.human_tracker = human_tracker
                self.human_bb = human_bbx
        return best_match

    def get_attempts(self):
        return self.attempts

    def kill(self):
        #return info about tracker can be implemented here
        return None

    def update(self, frame):
        bbxs = self.get_bboxes()
        failed_trackers = []
        constant_trackers = []
        trackers_to_delete = []
        for i, tracker in self.trackers.items():
            if i not in bbxs.keys():
                #this part is not in current human
                trackers_to_delete.append(i)
                continue
            ok, bbox = tracker.update(frame)
            if ok:
                #check if bbox is shifted
                if (bbox[0] - bbxs[i][0]) < 2 and (bbox[1] - bbxs[i][1]) < 2:
                    constant_trackers.append(i)
                bbxs[i] = bbox
            else:
                failed_trackers.append(i)
        self.human = self.bbxs2human(bbxs)
        for tracker_id in trackers_to_delete:
            del self.trackers[tracker_id]
        if self.use_whole_human_tracking:
            ok, human_bbox = self.human_tracker.update(frame)
            if ok:
                dx = human_bbox[0] - self.human_bb[0] #box shift
                dy = human_bbox[1] - self.human_bb[1]
                self.human_bb = human_bbox
                #if part tracking failed try to reinitialize with box shifted as main human box
                for tracker_id in failed_trackers:
                    if tracker_id in bbxs.keys():
                        old_bbox = bbxs[tracker_id]
                        new_bbox = [old_bbox[0]+dx, old_bbox[1]+dy, 
                                    old_bbox[2], old_bbox[3]]
                        self.trackers[tracker_id].init(frame, tuple(new_bbox))
                #if part tracker is bound with static backgorund reinitialize with box shifted as main human box
                for tracker_id in constant_trackers:
                    if tracker_id in bbxs.keys():
                        old_bbox = bbxs[tracker_id]
                        new_bbox = [old_bbox[0]+dx, old_bbox[1]+dy, 
                                    old_bbox[2], old_bbox[3]]
                        self.trackers[tracker_id].init(frame, tuple(new_bbox))

    def set_wh(self, w, h):
        self.w = w
        self.h = h

    def _gen_hid(self):
        hash = hashlib.sha1()
        hash.update(str(time.time()).encode('utf-8'))
        return hash.hexdigest()[:10]

    def set_hid(self, hid=None):
        #set human id in tracker
        if hid is None:
            hid = self._gen_hid()
        self.hid = hid
        return hid
    def get_hid(self):
        if hasattr(self, 'hid'):
            hid = self.hid
        else:
            hid = None
        return hid

    def _create_single_tracker(self, bbox):
        tracker_type = self.tracker_type
        if tracker_type == 'BOOSTING':
            tracker = cv2.TrackerBoosting_create()
        elif tracker_type == 'MIL':
            tracker = cv2.TrackerMIL_create()
        elif tracker_type == 'KCF':
            tracker = cv2.TrackerKCF_create()
        elif tracker_type == 'TLD':
            tracker = cv2.TrackerTLD_create()
        elif tracker_type == 'MEDIANFLOW':
            tracker = cv2.TrackerMedianFlow_create()
        elif tracker_type == 'GOTURN':
             tracker = cv2.TrackerGOTURN_create()
        elif tracker_type == 'MOSSE':
            tracker = cv2.TrackerMOSSE_create()
        else:
            raise ValueError('{} is invalid tracker type name'.format(tracker_type))
        return tracker

    def _get_base_dim(self, k = 0.5):
        #defin bbox size by computing length of limbs (ankle->knee, wrist->elbow)
        #bbox will have a size of k * mean limb length

        human = self.human
        #human parts in coco pairs:
        parts = [2, 3, 4, 5, #arms
                 7, 8, 10, 11] # legs
        selected_pairs = [CocoPairs[i] for i in parts]
        limb_lengths = []
        for pair in  selected_pairs:
            part_u, part_v = pair
            if part_u in human.body_parts.keys() and part_v in human.body_parts.keys():
                leng  = self._body_parts_distance(human.body_parts[part_u],
                                                  human.body_parts[part_v])
                limb_lengths.append(leng)
        if len(limb_lengths):
            return int(k * np.mean(limb_lengths) + 0.5)
        else:
            return None
    def _bbox_center(self, bbox):
        #compute center of bbox as single point, bbox given as (p1x, p1y, w, h)
        cx = int(bbox[0] + bbox[2] / 2 + 0.5)
        cy = int(bbox[1] + bbox[3] / 2 + 0.5)
        return cx, cy

    def _body_parts_distance(self, part, other_part):
        if not hasattr(self, 'w') or not hasattr(self, 'h'):
            raise AttributeError('Please, set image size with set_wh first')
        w, h = self.w, self.h
        #normalized distances:
        dx = np.abs(part.x - other_part.x)
        dy = np.abs(part.y - other_part.y)
        #distance in pixels
        rdx, rdy = w * dx, h * dy
        return (rdx ** 2 + rdy **2) ** 0.5

    def _whole_human_bb(self):
        human = self.human
        w, h = self.w, self.h
        base_size = self._get_base_dim()
        if base_size is None:
            return None
        k = 0
        margin = k * base_size
        #find max, min x, y and add margin k * base_dim
        xs = [w * part.x for part in human.body_parts.values()]
        ys = [h * part.y for part in human.body_parts.values()]
        tlx = max([min(xs) - margin, 0])
        tly = max([min(ys) - margin, 0])
        brx = min([max(xs) + margin, w])
        bry = min([max(ys) + margin, h])
        bbx = [tlx, tly, brx - tlx, bry - tly]
        print(bbx)
        return bbx

    def get_bboxes(self):
        #return a list of bounding boxes for each part of current human
        human = self.human
        w, h = self.w, self.h
        k = 2
        base_size = self._get_base_dim()
        bbxs = {}
        if base_size is None:
            return bbxs
        bbs = k * base_size #bounding rectangle siede size
        for part_id, part in human.body_parts.items():
            cx, cy = int(w * part.x + 0.5), int(h * part.y + 0.5)
            tlx = cx - bbs // 2
            tly = cy - bbs // 2
            bbx = [tlx, tly, bbs, bbs]
            bbxs[part_id] = bbx
        return bbxs

    def get_human(self):
        return self.human

    def bbxs2human(self, bbxs):
        human = self.human
        w, h = self.w, self.h
        for box_id, bbox in bbxs.items():
            if box_id in human.body_parts.keys():
                cx, cy = self._bbox_center(bbox)
                human.body_parts[box_id].x = cx / w
                human.body_parts[box_id].y = cy / h
        return human

    def get_distance(self, other_human):
        #compute distance between tracker status and other human
        ar = np.asarray
        if not hasattr(self, 'human'):
            raise AttributeError('Tracker should be initialized first')
        human = self.human
        w, h = self.w, self.h
        #to compensate lack of part of human in other human, mean is computed,
        #then is multiplied 17 times (17 keypoints)
        part_ids = set(human.body_parts.keys())
        other_part_ids = set(other_human.body_parts.keys())
        common_part_ids = part_ids.intersection(other_part_ids)
        dists = np.empty(0)
        for part_id in common_part_ids:
            bp_pos = ar([w * human.body_parts[part_id].x, h * human.body_parts[part_id].y])# part pos
            obp_pos = ar([w * other_human.body_parts[part_id].x, h * other_human.body_parts[part_id].y])# other part pos
            dist = np.linalg.norm(obp_pos - bp_pos)
            dists = np.append(dists, dist)
        mean_dist = np.mean(dists)
        return 17 * mean_dist
    def draw_bboxes(self, frame):
        #visualize current bboxes state
        vis_frame = np.copy(frame)
        bbxs = self.get_bboxes()
        for _, bbox in bbxs.items():
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0]) + int(bbox[2]), int(bbox[1]) + int(bbox[3]))
            cv2.rectangle(vis_frame, p1, p2, (0,255,0), 2, 1)
        return vis_frame
    def draw_id(self, frame):
        vis_frame = np.copy(frame)
        bbxs = self.get_bboxes()
        #compute center of person
        if len(bbxs) == 0:
            return vis_frame
        meanx, meany = np.round(np.mean(([[box[0], box[1]]
                                 for box in bbxs.values()]),
                                axis = 0)).astype(np.int)
        text_id = self.hid
        font = cv2.FONT_HERSHEY_DUPLEX
        color = self.color
        vis_frame = cv2.putText(vis_frame, text_id, (meanx, meany), font, 1, color.tolist(), 2, cv2.LINE_AA)
        return vis_frame

    def draw_human_bbox(self, frame):
        vis_frame = np.copy(frame)
        bbox = self.human_bb
        color = self.color
        p1 = (int(bbox[0]), int(bbox[1]))
        p2 = (int(bbox[0]) + int(bbox[2]), int(bbox[1]) + int(bbox[3]))
        cv2.rectangle(vis_frame, p1, p2, color.tolist(), 2, 1)
        return vis_frame

if __name__ == '__main__':
    #run 'run.py' to obtain variables

    hT = HumanTracker()
    gT = GroupTracker()
    humans = e.inference(image, resize_to_default=True, upsample_size=4.0)
    initialized_humans = gT.init(humans, image)
    logger.debug('Initialized: {}'.format(initialized_humans))
    vis_image = gT.draw_boxes(image)
    #human = humans[0]
    #hT.init(human, image)
    #hT.set_hid()
    #vis_image = hT.draw_bboxes(image)
    plt.imshow(vis_image)
    plt.show()
    for i in range(1, 82):
        new_image =  np.roll(image, 10*i, axis = 1)
        if i % 10 != 0:
            #hT.update(new_image)
            gT.update(new_image)
        else:
            humans = e.inference(new_image, resize_to_default=True, upsample_size=4.0)
            new_humans, cur_humans, old_humans = gT.reinit(humans,new_image)
            logger.warn('New: {} current: {} Removed: {}'.format(new_humans, cur_humans, old_humans))
            #hT.reinit(humans, new_image)
            new_image = TfPoseEstimator.draw_humans(new_image, humans, imgcopy=False)

        vis_image = gT.draw_boxes(new_image)

        plt.imshow(vis_image)
        plt.show()
