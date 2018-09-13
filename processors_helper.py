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

from common.settings import HUMAN_POSE_TAG
from common.settings import HUMAN_COUNTER_TAG
from common.settings import PLATES_PROC_TAG
from common.settings import PLATES_AGR_TAG

from processor.human_pose import HumanPoseLocalizer
from processor.plates_proc import PlatesLocalizer
from agregator.human_counter import AgregatorHumanCounter
from agregator.plates_agr import AgregatorPlates


PROCESSORS = {
    HUMAN_POSE_TAG: {
        'callback': HumanPoseLocalizer,
    },
    PLATES_PROC_TAG: {
        'callback': PlatesLocalizer,
    },
}
    
AGREGATORS = {
    HUMAN_COUNTER_TAG: {
        'callback': AgregatorHumanCounter,        
    },
    PLATES_AGR_TAG: {
        'callback': AgregatorPlates,        
    },
}
    
