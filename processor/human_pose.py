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
from processor.processor_base import ProcessorBase
from common.settings import HUMAN_POSE_TAG

class HumanPoseLocalizer(ProcessorBase):
    def __init__(self, logger, image_queues, pipe_starts,  **kwargs):
        self.name = HUMAN_POSE_TAG
        self.inference_module_name = 'processor.detector_base.tf_pose.estimator'
        self.inference_class_name = 'TfPoseEstimator'
        self.weights_file = 'human_pose_light.pb'
        ProcessorBase.__init__(self, logger, image_queues, pipe_starts,  **kwargs)
