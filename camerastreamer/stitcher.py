import time
import logging
import threading
import subprocess
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

    def stitch(self, pattern):
        old_feedrate = self.printer.feedrate
        work_folder_name = time.strftime("%d-%m-%y--%X")
        self.clean_tmp_folder("./tmp/stitch")
        work_path = self.check_tmp_folder(work_folder_name)
        self.printer.set_feedrate(100)
        self.image_list = []
        start_time = time.time()
        if pattern == 0:
            self.get_images_list_2_pattern(work_path)
        else:
            self.get_images_list_Z_pattern(work_path)
        print(self.image_list)
        self.run_stitch(work_path)
        elapsed_s = time.time() - start_time
        logging.info(f"[STITCHER] Done total time: {elapsed_s} s")
        return f"{work_path}/single/out.jpg"

    def focus_stack_stitch(self, pattern):
        old_feedrate = self.printer.feedrate
        work_folder_name = time.strftime("%d-%m-%y--%X")
        self.clean_tmp_folder("./tmp/stitch")
        work_path = self.check_tmp_folder(work_folder_name)
        self.printer.set_feedrate(100)
        start_time = time.time()
        if pattern == 0:
            self.get_fs_image_list_2_pattern(3, work_path=work_path)
        else:
            self.get_fs_image_list_Z_pattern(3, work_path=work_path)
        self.run_stitch(work_path)
        elapsed_s = time.time() - start_time
        logging.info(f"[STITCHER-FS] Done total time: {elapsed_s} s")
        return f"{work_path}/single/out.jpg"

    def get_images_list_2_pattern(self, work_path, wait_per_frame=3):
        photo_name = ""
        old_xPos = self.printer.xPos
        old_yPos = self.printer.yPos
        step_xAxis = self.step_per_fov
        step_yAxis = (self.step_per_fov * 3) / 4  # keep aspect ratio as images are 4/3
        logging.info(f"[STITCHER2]: Capturing {self.fovs[0]}x{self.fovs[1]} FoVs")
        for i in range(0, self.fovs[1]):
            for j in range(0, self.fovs[0]):
                self.autofocus.auto_focus_fine()
                time.sleep(wait_per_frame)
                sample = self.camera.get_opencv_from_stream()
                if j < self.fovs[0] - 1:
                    self.printer.move_xAxis(step_xAxis)
                photo_name = photo_name = self.get_photo_name(i, j, 0)
                logging.info(f"[STITCHER2]: Saving {photo_name}")
                cv2.imwrite(f"{work_path}/{photo_name}", sample)
                self.image_list.append(f"{photo_name}")
            step_xAxis = -step_xAxis
            logging.info(f"[STITCHER2]: 2 Pattern changing xStep to: {step_xAxis}")
            self.printer.move_yAxis(-step_yAxis)
            time.sleep(1)

        self.printer.set_xPos(old_xPos)
        self.printer.set_yPos(old_yPos)
        

    def get_images_list_Z_pattern(self, work_path, wait_per_frame=3):
        photo_name = ""
        old_xPos = self.printer.xPos
        old_yPos = self.printer.yPos
        step_xAxis = self.step_per_fov
        step_yAxis = (self.step_per_fov * 3) / 4  # keep aspect ratio as images are 4/3
        logging.info(f"[STITCHERZ]: Capturing {self.fovs[0]}x{self.fovs[1]} FoVs")
        for i in range(0, self.fovs[1]):
            for j in range(0, self.fovs[0]):
                self.autofocus.auto_focus_fine()
                time.sleep(wait_per_frame)
                sample = self.camera.get_opencv_from_stream()
                if j < self.fovs[0] - 1:
                    self.printer.move_xAxis(step_xAxis)
                photo_name = photo_name = self.get_photo_name(i, j, 1)                  
                logging.info(f"[STITCHERZ]: Saving {photo_name}")
                cv2.imwrite(f"{work_path}/{photo_name}", sample)
                self.image_list.append(photo_name)
            self.printer.set_xPos(old_xPos)
            self.printer.move_yAxis(-step_yAxis)
            time.sleep(1)

        self.printer.set_xPos(old_xPos)
        self.printer.set_yPos(old_yPos)

    def get_fs_image_list_2_pattern(self, wait_per_frame, work_path):
        images = []
        focus_stack = FocusStack()
        old_xPos = self.printer.xPos
        old_yPos = self.printer.yPos
        step_xAxis = self.step_per_fov
        step_yAxis = (self.step_per_fov * 3) / 4  # keep aspect ratio as images are 4/3
        logging.info(f"[STITCHER-FS2]: Capturing FS {self.fovs[0]}x{self.fovs[1]} FoVs")
        for i in range(0, self.fovs[1]):
            self.create_work_folder(work_path, i)
            for j in range(0, self.fovs[0]):
                work_folder = self.create_work_folder(f"{work_path}/{i}", j)
                self.autofocus.auto_focus_fine()
                time.sleep(wait_per_frame)
                focus_stack.capture_samples(3, work_folder)  # image capture
                self.threads_list.append(
                    threading.Thread(
                        target=self._thread_focus_stack,
                        args=(work_path, work_folder, i, j,0),
                    )
                )  # focus stack processing
                self.threads_list[j + (i * self.fovs[1])].start()
                if j < self.fovs[0] - 1:
                    self.printer.move_xAxis(step_xAxis)

            step_xAxis = -step_xAxis
            logging.info(f"[STITCHER-FS2]: 2 Patern changing xStep to: {step_xAxis}")
            self.printer.move_yAxis(-step_yAxis)
            time.sleep(1)
        self.wait_threads()
        self.printer.set_xPos(old_xPos)
        self.printer.set_yPos(old_yPos)
        
    def get_fs_image_list_Z_pattern(self, wait_per_frame, work_path):
        images = []
        focus_stack = FocusStack()
        old_xPos = self.printer.xPos
        old_yPos = self.printer.yPos
        step_xAxis = self.step_per_fov
        step_yAxis = (self.step_per_fov * 3) / 4  # keep aspect ratio as images are 4/3
        logging.info(f"[STITCHER-FSZ]: Capturing FS {self.fovs[0]}x{self.fovs[1]} FoVs")
        for i in range(0, self.fovs[1]):
            self.create_work_folder(work_path, i)
            for j in range(0, self.fovs[0]):
                work_folder = self.create_work_folder(f"{work_path}/{i}", j)
                self.autofocus.auto_focus_fine()
                time.sleep(wait_per_frame)
                focus_stack.capture_samples(3, work_folder)  # image capture
                self.threads_list.append(
                    threading.Thread(
                        target=self._thread_focus_stack,
                        args=(work_path, work_folder, i, j,1),
                    )
                )  # focus stack processing
                self.threads_list[j + (i * self.fovs[1])].start()
                if j < self.fovs[0] - 1:
                    self.printer.move_xAxis(step_xAxis)

            self.printer.set_xPos(old_xPos)
            self.printer.move_yAxis(-step_yAxis)
            time.sleep(1)
        self.wait_threads()
        self.printer.set_xPos(old_xPos)
        self.printer.set_yPos(old_yPos)

    def _thread_focus_stack(self, work_path, work_folder, row, column,pattern):
        focus_stack = FocusStack()
        output_path = focus_stack.run_focus_stack(work_folder)
        result = cv2.imread(output_path, 1)
        photo_name = self.get_photo_name(row, column,pattern)
        cv2.imwrite(f"{work_path}/{photo_name}", result)
        self.image_list.append(f"{photo_name}")
        logging.info(f"[STITCHER-FS]: Saving {photo_name}")

    def get_photo_name(self,row, column,pattern):
        if pattern == 0:
            if row % 2:
                # impar
                photo_name = f"c{format(self.fovs[0]-1-column,'04')}_r{format(row,'04')}.tif"
            else:
                photo_name = f"c{format(column,'04')}_r{format(row,'04')}.tif"
        else:
            photo_name = f"c{format(column,'04')}_r{format(row,'04')}.tif"
        return photo_name

    def wait_threads(self):
        for thread in self.threads_list:
            thread.join()
        logging.info(f"[STITCHER]: Threads joined")

    def run_stitch(self, work_path):
        args = ["xy-stitch"] + self.image_list
        status = subprocess.run(args, cwd=work_path)
        args = ["xy-ts"] + ["--ignore-crop"]
        status = subprocess.run(args, cwd=work_path)

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
