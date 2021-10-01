import time
import logging
import subprocess
import cv2
import io
import os
import shutil
from camerastreamer.camera_streamer import CameraStreamer
from camerastreamer.focus_stack import FocusStack
from camerastreamer.auto_focus import AutoFocus
from communications.printer_com import Printer
from communications.arduino_com import Arduino

# invokes focus-stack utility by https://github.com/PetteriAimonen/focus-stack


class Filter:
    def __init__(self):
        self.camera = CameraStreamer.get_instance()
        self.printer = Printer.get_instance()
        self.autofocus = AutoFocus()
        self.focus_stack = FocusStack()

    def filter(self, filter):
        if filter == "color":
            return self.get_color_corrected()
        else:
            return None

    def filter_fs(self, filter, n_focus):
        if filter == "color":
            return self.get_color_corrected(n_focus)
        else:
            return None

    def get_color_corrected(self, n_focus=None):
        logging.info(f"[FILTER] Capturing color corrected photo")
        if n_focus is None:
            og_img = self.camera.get_opencv_photo()
            logging.info(f"[FILTER] OG photo taken")
        else:
            og_img = cv2.imread(self.focus_stack.get_focus_stack_img(n_focus))
            logging.info(f"[FILTER] OG focus stacked photo taken")
        self.printer.move_zAxis(-0.7)
        time.sleep(0.5)
        back_img = self.camera.get_opencv_photo()
        logging.info(f"[FILTER] Background photo taken")
        self.printer.move_zAxis(0.7)
        self.autofocus.auto_focus_fine()
        fil_img = og_img / back_img
        logging.info(f"[FILTER] Filtered photo OK")
        norm_img = cv2.normalize(fil_img, None, 0, 255, cv2.NORM_MINMAX)
        status, jpg_img = cv2.imencode(".jpg", norm_img)
        logging.info(f"[FILTER] Filtered photo encoded")
        return io.BytesIO(jpg_img)
