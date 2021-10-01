import time
import io
import threading
import logging
import cv2
import numpy as np
from picamerax import PiCamera

# This code is based on examples provided by Miguel Grinberg: https://github.com/miguelgrinberg/flask-video
# Miguel has an extremely thorough tutorial on how to stream video with Flask here:
# https://blog.miguelgrinberg.com/post/video-streaming-with-flask


class CameraStreamer:
    __instance__ = None

    def __init__(self):
        if CameraStreamer.__instance__ is None:
            self.capture_thread = (
                None  # background thread that reads frames from camera
            )
            self.frame = None  # current frame is stored here by background thread
            self.last_access = 0  # time of last client access to the camera
            self.stop = False
            self.lock = threading.Lock()
            self.photo_mode = False
            self.camera = PiCamera()
            self.photo_resolution = (4056, 3040)
            self.stream_resolution = (1640, 1232)
            # self.stream_resolution = (960, 720)
            # lock init
            self.lock.acquire()
            CameraStreamer.__instance__ = self
        else:
            raise Exception("Only one camera can be created at any given time")

    @staticmethod
    def get_instance():
        if not CameraStreamer.__instance__:
            CameraStreamer()
        return CameraStreamer.__instance__

    def start_thread(self):
        if self.capture_thread is not None and not self.capture_thread.is_alive():
            self.capture_thread = None
            logging.info("Capture Thread ended but wasn't deleted")

        if self.capture_thread is None:
            logging.info("[CAPTURE_THREAD] Starting")
            # start background frame thread
            self.stop = False
            self.capture_thread = threading.Thread(target=self._thread)
            self.capture_thread.start()

            # wait until frames start to be available
            while self.frame is None:
                time.sleep(0)

    def stop_thread(self):
        if self.capture_thread is None:

            pass
        else:
            logging.info("[CAMERA]Trying to kill Capture Thread")
            self.stop = True
            self.capture_thread.join()
            time.sleep(0.1)
            self.capture_thread = None
            logging.info("[CAMERA]Capture Thread joined")

    def get_frame(self):
        self.last_access = time.time()
        if not self.photo_mode:
            self.start_thread()

        # wait until new frame is available
        # self.lock.acquire(True)
        return self.frame

    def _thread(self):
        # camera initial setup
        logging.info("[CAPTURE_THREAD] Start")
        # self.camera.start_recording(stream, format='mjpeg'

        self.camera.resolution = self.stream_resolution
        self.camera.hflip = False
        self.camera.vflip = False

        # let camera warm up
        # self.camera.start_preview()
        # time.sleep(.5)
        # self.camera.stop_preview()
        stream = io.BytesIO()
        for foo in self.camera.capture_continuous(stream, "jpeg", use_video_port=True):
            # store frame
            stream.seek(0)
            self.frame = stream.read()

            # release lock as new frame is available
            # if not self.lock.acquire(False):
            #    self.lock.release()
            # reset stream for next frame

            stream.seek(0)
            stream.truncate()
            if self.stop:
                break
                # if there hasn't been any clients asking for frames in
                # the last 10 seconds stop the thread
            if time.time() - self.last_access > 10:
                break

        self.stop = False
        logging.info("[CAPTURE_THREAD] Ended")

    def get_photo(self):
        self.photo_mode = True
        self.stop_thread()
        self.camera.resolution = self.photo_resolution
        self.camera.sharpness = 75
        output = io.BytesIO()
        self.camera.capture(output, "jpeg")
        output.seek(0)
        logging.info(f"[CAMERA] Photo taken")
        time.sleep(0.2)
        self.photo_mode = False
        return output

    def save_photo(self, filepath="./tmp/1.jpeg"):
        self.photo_mode = True
        self.stop_thread()
        self.camera.resolution = self.photo_resolution
        self.camera.sharpness = 50
        self.camera.capture(filepath, "jpeg")
        logging.info(f"[CAMERA] Local Photo taken")
        time.sleep(0.2)
        self.photo_mode = False

    def get_opencv_photo(self):
        self.photo_mode = True
        self.stop_thread()
        self.camera.resolution = self.photo_resolution
        output = io.BytesIO()
        self.camera.capture(output, "jpeg")
        self.photo_mode = False
        data = np.fromstring(output.getvalue(), dtype=np.uint8)
        image = cv2.imdecode(data, 1)
        return image

    def get_opencv_from_stream(self):
        output = self.get_frame()
        data = np.fromstring(output, dtype=np.uint8)
        image = cv2.imdecode(data, 1)
        return image

    def get_lapacian(self):
        image = self.get_opencv_from_stream()
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(grayscale, cv2.CV_64F).var()

    def get_frame_size(self):
        output = self.get_frame()
        return len(output)

    def change_stream_resolution(self, new_resolution):
        self.photo_mode = True
        self.stop_thread()
        self.stream_resolution = new_resolution
        self.camera.resolution = self.stream_resolution
        self.photo_mode = False
