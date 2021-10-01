import time
import logging
import threading
import cv2
import os
import shutil
from camerastreamer.camera_streamer import CameraStreamer
from camerastreamer.auto_focus import AutoFocus
from camerastreamer.focus_stack import FocusStack
from communications.printer_com import Printer
from communications.arduino_com import Arduino


class Stitcher:
    def __init__(self, fov_x=3, fov_y=3, step_per_fov=0.7):
        self.camera = CameraStreamer.get_instance()
        self.printer = Printer.get_instance()
        self.arduino = Arduino.get_instance()
        self.autofocus = AutoFocus()
        self.fovs = [fov_x, fov_y]  # X,Y
        self.step_per_fov = step_per_fov
        self.image_list = []
        self.threads_list = []

    def stitch(self, threaded):
        if threaded:
            return self._stitch_threaded()
        else:
            return self._stitch()

    def _stitch_threaded(self):
        old_feedrate = self.printer.feedrate
        work_folder_name = time.strftime("%d-%m-%y--%X")
        work_path = self.check_tmp_folder(work_folder_name)
        self.printer.set_feedrate(100)
        self.clean_tmp_folder("./tmp/stitch")

        self.get_images_list_threaded()
        stitcher = cv2.Stitcher_create(mode=1)  # 0 panorama 1 scan
        stitcher.setPanoConfidenceThresh(0.3)
        (status, stitched) = stitcher.stitch(self.image_list)

        logging.info(f"[STITCHER]: Panorama status{status}")
        if status == 0:
            cv2.imwrite(f"{work_path}/o.png", stitched)
            return f"{work_path}/o.png"
        else:
            return "error"

    def _stitch(self):
        old_feedrate = self.printer.feedrate
        work_folder_name = time.strftime("%d-%m-%y--%X")
        work_path = self.check_tmp_folder(work_folder_name)
        self.printer.set_feedrate(100)
        self.clean_tmp_folder("./tmp/stitch")
        start_time = time.time()
        self.get_images_list()
        stitcher = cv2.Stitcher_create(mode=1)  # 0 panorama 1 scan
        stitcher.setPanoConfidenceThresh(0.2)
        (status, stitched) = stitcher.stitch(self.image_list)
        elapsed_s = time.time() - start_time
        logging.info(f"[INFERENCE] Done total time: {elapsed_s} s")
        logging.info(f"[STITCHER]: Panorama status{status}")
        if status == 0:
            cv2.imwrite(f"{work_path}/o.png", stitched)
            return f"{work_path}/o.png"
        else:
            return "error"

    def focus_stack_stitch(self):
        old_feedrate = self.printer.feedrate
        work_folder_name = time.strftime("%d-%m-%y--%X")
        work_path = self.check_tmp_folder(work_folder_name)
        self.printer.set_feedrate(100)
        self.clean_tmp_folder("./tmp/stitch")

        start_time = time.time()
        self.get_fs_image_list(3, work_path=work_path)
        stitcher = cv2.Stitcher_create(mode=1)  # 0 panorama 1 scan
        stitcher.setPanoConfidenceThresh(0.1)
        (status, stitched) = stitcher.stitch(self.image_list)
        elapsed_s = time.time() - start_time
        logging.info(f"[INFERENCE] Done total time: {elapsed_s} s")
        logging.info(f"[STITCHER]: Panorama status{status}")
        if status == 0:
            cv2.imwrite(f"{work_path}/o.png", stitched)
            return f"{work_path}/o.png"
        else:
            return "error"

    def get_images_list_threaded(self, wait_per_frame=3):
        # Too much error kept for archive reasons
        old_xPos = self.printer.xPos
        old_yPos = self.printer.yPos
        self.autofocus.auto_focus_lap()
        logging.info(f"[STITCHER]: Capturing {self.fovs[0]}x{self.fovs[1]} FoVs")
        for i in range(0, self.fovs[1]):
            images = []
            for j in range(0, self.fovs[0]):
                self.printer.move_xAxis(self.step_per_fov)
                time.sleep(wait_per_frame)
                self.autofocus.auto_focus_fine()
                images.append(self.camera.get_opencv_from_stream())
            self.threads_list.append(
                threading.Thread(target=self._thread_stitch, args=(images, i))
            )
            self.threads_list[i].start()
            self.printer.set_xPos(old_xPos)
            self.printer.move_yAxis(self.step_per_fov)
            time.sleep(2)

        self.wait_threads()
        self.printer.set_xPos(old_xPos)
        self.printer.set_yPos(old_yPos)

    def get_images_list(self, wait_per_frame=3):
        old_xPos = self.printer.xPos
        old_yPos = self.printer.yPos
        step_xAxis = self.step_per_fov
        step_yAxis = (self.step_per_fov * 3) / 4  # keep aspect ratio as images are 4/3
        logging.info(f"[STITCHER]: Capturing {self.fovs[0]}x{self.fovs[1]} FoVs")
        for i in range(0, self.fovs[1]):
            for j in range(0, self.fovs[0]):
                self.autofocus.auto_focus_fine()
                time.sleep(wait_per_frame)
                sample = self.camera.get_opencv_photo()
                self.image_list.append(sample)
                logging.info(f"[STITCHER]: Sample [{i}]x[{j}] taken")
                if j < self.fovs[0] - 1:
                    self.printer.move_xAxis(step_xAxis)
                cv2.imwrite(f"tile_{j+(i*self.fovs[1])}.png", sample)
            step_xAxis = -step_xAxis
            logging.info(f"[STITCHER]: 2 Patern changing xStep to: {step_xAxis}")
            self.printer.move_yAxis(step_yAxis)
            time.sleep(2)

        self.printer.set_xPos(old_xPos)
        self.printer.set_yPos(old_yPos)

    def get_fs_image_list(self, wait_per_frame, work_path):
        images = []
        focus_stack = FocusStack()
        old_xPos = self.printer.xPos
        old_yPos = self.printer.yPos
        step_xAxis = self.step_per_fov
        step_yAxis = (self.step_per_fov * 3) / 4  # keep aspect ratio as images are 4/3
        logging.info(f"[STITCHER]: Capturing FS {self.fovs[0]}x{self.fovs[1]} FoVs")
        for i in range(0, self.fovs[1]):
            self.create_work_folder(work_path, i)
            for j in range(0, self.fovs[0]):

                work_folder = self.create_work_folder(f"{work_path}/{i}", j)
                # time.sleep(wait_per_frame)
                focus_stack.capture_samples(3, work_folder)
                output_path = focus_stack.run_focus_stack(work_folder)
                images.append(output_path)
                if j < self.fovs[0] - 1:
                    self.printer.move_xAxis(step_xAxis)
                # self.threads_list.append(threading.Thread(target=self._thread_fs, args=(work_folder,j+(i*self.fovs[1]))))
                # self.threads_list[j+(i*self.fovs[1])].start()
            step_xAxis = -step_xAxis
            self.printer.move_yAxis(step_yAxis)
            time.sleep(1.5)

        # self.wait_threads()
        # convert fs results path to mat objects
        self.image_list = self.read_fs_results(images)
        self.printer.set_xPos(old_xPos)
        self.printer.set_yPos(old_yPos)

    def _thread_stitch(self, images, row):
        logging.info(f"[STITCHER{row}]: Image ok")
        stitcher = cv2.Stitcher_create(mode=1)  # 0 panorama 1 scan
        stitcher.setPanoConfidenceThresh(0.2)
        (status, stitched) = stitcher.stitch(images)
        logging.info(f"[STITCHER{row}]: Status {status}")
        if status == 0:
            self.image_list.append(stitched)
            # cv2.imwrite(f'o{row}.png',stitched)

    def _thread_fs(self, work_folder, row):
        # Thread for focus stacking a list of images,
        # Doesn't work as fs is already threaded and having multiples fs open blocks the pi
        logging.info(f"[STITCHER FS {row}]: Image ok")
        focus_stack = FocusStack()
        output_path = focus_stack.run_focus_stack(work_folder)
        logging.info(f"[STITCHER FS {row}]: Status focus stack OK")
        self.image_list.append(output_path)

    def wait_threads(self):
        for thread in self.threads_list:
            thread.join()
        logging.info(f"[STITCHER]: Threads joined")

    def read_fs_results(self, images_path):
        images = []
        for image in images_path:
            images.append(cv2.imread(image, 1))
        return images

    def check_tmp_folder(self, dir_path):
        if not os.path.exists(f"./tmp/stitch/{dir_path}"):
            os.mkdir(f"./tmp/stitch/{dir_path}")
        return f"./tmp/stitch/{dir_path}"

    def clean_tmp_folder(self, dir_path):
        # checks if >10 items in dir_path and deletes them
        folder_list = os.listdir(dir_path)
        if len(folder_list) > 10:
            for folder_name in folder_list[:10]:
                shutil.rmtree(os.path.join(dir_path, folder_name))

    def create_work_folder(self, dir_path, index):
        if not os.path.exists(f"{dir_path}/{index}"):
            os.mkdir(f"{dir_path}/{index}")
        return f"{dir_path}/{index}"
