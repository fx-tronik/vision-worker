import numpy as np
import cv2
from processor.detector_base.plates.config import Config
import processor.detector_base.plates.model as modellib
import processor.detector_base.plates.detekcja_OCR as detekcja_OCR
import tensorflow as tf


class InferenceConfig(Config):
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    NAME = "plates"
    NUM_CLASSES = 1 + 1  # background + ` shapes
    IMAGE_MIN_DIM = 1024
    IMAGE_MAX_DIM = 1600
    RPN_ANCHOR_SCALES = (4, 8, 16, 32, 64)  # anchor side in pixels
    # Ratios of anchors at each cell (width/height)
    # A value of 1 represents a square anchor, and 0.5 is a wide anchor
    RPN_ANCHOR_RATIOS = [0.5, 1, 2]
    POST_NMS_ROIS_INFERENCE = 500
    RPN_NMS_THRESHOLD = 0.8
    # Minimum probability value to accept a detected instance
    # ROIs below this threshold are skipped
    DETECTION_MIN_CONFIDENCE = 0.9

    # Non-maximum suppression threshold for detection
    DETECTION_NMS_THRESHOLD = 0.3


class PlatesOCR:
    def __init__(self, path):
        config = tf.ConfigProto(allow_soft_placement=True)
        config.gpu_options.allow_growth=True

        self.session1 = tf.Session(config=config)
        with self.session1.as_default():
            self.inference_config = InferenceConfig()
            self.model = modellib.MaskRCNN(mode="inference",
                              config=self.inference_config,
                              model_dir='logs/')
            self.model.load_weights(path + 'plates.h5', by_name=True)

        self.session2 = tf.Session(config=config)
        with self.session2.as_default():
            self.model_ocr = detekcja_OCR.predict(self.session2, path + 'ocr.hdf5')

    def __del__(self):
        # self.persistent_sess.close()
        pass

    def inference(self, image):
        with self.session1.as_default():
            results = self.model.detect([image], verbose=0)
        res = results[0]
        masks = res['masks']
        corners = []

        for i in range(masks.shape[2]):
            img, contours, hierarchy = cv2.findContours(masks[:,:,i].astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for con in contours:
                rect = cv2.minAreaRect(np.array(con))
                if(rect[1][1] * rect[1][0] < 100):      # w*h jesli obszar mniejszy niz 100 pikseli to pominac
                    continue
                bbox = cv2.boxPoints(rect).astype(int)
                if(rect[1][1] > rect[1][0]):            # if w > h
                    bbox = np.array([bbox[1], bbox[2], bbox[3], bbox[0]])
                corners.append(bbox)
        #return corners, res['scores']

        plate_size = (520, 120)
        pts_tablica = np.array([[0,plate_size[1]], [0,0], [plate_size[0],0], [plate_size[0], plate_size[1]]])

        ocr_znaki = []
        for i, cor in enumerate(corners):
            M = cv2.getPerspectiveTransform(cor.astype(np.float32), pts_tablica.astype(np.float32))
            tablica = cv2.warpPerspective(image, M, plate_size)

            with self.session2.as_default():
                model_znaki = self.model_ocr.ocr(tablica)
                ocr_znaki.append(model_znaki)
        for cor in corners:
              cv2.drawContours(image, [cor], -1, (0,255,0), 1)
        cv2.imwrite("debug_ocr.jpg", image)

        return ocr_znaki, corners
