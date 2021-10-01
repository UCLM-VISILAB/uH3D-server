import time
import logging
import subprocess
import cv2
import os
import shutil
from camerastreamer.camera_streamer import CameraStreamer
from camerastreamer.auto_focus import AutoFocus
from communications.printer_com import Printer
from communications.arduino_com import Arduino

# invokes focus-stack utility by https://github.com/PetteriAimonen/focus-stack


class FocusStack:
    def __init__(self):
        self.camera = CameraStreamer.get_instance()
        self.printer = Printer.get_instance()
        self.autofocus = AutoFocus()

    def get_focus_stack_img(self, n_focus=3, step=0.02):
        # returns the path of the focus stacked image
        logging.info(f"[FOCUSSTACK] Capturing {n_focus} focus samples")
        self.clean_tmp_folder("./tmp/fs")
        work_folder_name = time.strftime("%d-%m-%y--%X")
        work_path = self.check_tmp_folder(work_folder_name)
        self.capture_samples(n_focus, step, work_path)
        output_path = self.run_focus_stack(work_path)
        logging.info(f"[FOCUSSTACK] Focus stack result {output_path}")
        return output_path

    def run_focus_stack(self, work_path="./tmp"):
        photo_list = self.get_photo_list(work_path)
        args = ["focus-stack"] + photo_list + [f"--output={work_path}/o.jpeg"]
        status = subprocess.run(args)
        logging.info(
            f"[FOCUSSTACK] Focus stack ended with {status.returncode} return code"
        )
        output_path = f"{work_path}/o.jpeg"
        if status.returncode != 0:
            output_path = f"{work_path}/0.jpeg"
        return output_path

    def capture_samples(self, n_focus, step, work_path):
        self.autofocus.auto_focus_fine()
        focus_per_side = (
            n_focus // 2
        )  # same number of focus sample upwards as downwards
        logging.info(f"[FOCUSSTACK] Main sample taken")
        self.camera.save_photo(filepath=f"{work_path}/0.jpeg")  # max focus sample
        # upwards
        for i in range(1, focus_per_side + 1):
            self.camera.save_photo(filepath=f"{work_path}/{i}.jpeg")
            logging.info(f"[FOCUSSTACK] Upward sample {i} taken")
            self.printer.move_zAxis(step)
            time.sleep(1)
        self.printer.move_zAxis(-step * focus_per_side)
        # downwards
        for i in range(1, focus_per_side + 1):
            self.camera.save_photo(filepath=f"{work_path}/{-i}.jpeg")
            logging.info(f"[FOCUSSTACK] Downward sample {i} taken")
            self.printer.move_zAxis(-step)
            time.sleep(1)
        self.printer.move_zAxis(step * focus_per_side)

    def check_tmp_folder(self, dir_path):
        if not os.path.exists(f"./tmp/fs/{dir_path}"):
            os.mkdir(f"./tmp/fs/{dir_path}")
        return f"./tmp/fs/{dir_path}"

    def get_photo_list(self, work_path):
        file_list = []
        for root, dirs, files in os.walk(work_path):
            for name in files:
                if ".jpeg" in name:
                    file_list.append(os.path.join(root, name))
        return file_list

    def clean_tmp_folder(self, dir_path):
        # checks if >10 items in dir_path and deletes them
        folder_list = os.listdir(dir_path)
        if len(folder_list) > 10:
            for folder_name in folder_list[:10]:
                shutil.rmtree(os.path.join(dir_path, folder_name))
