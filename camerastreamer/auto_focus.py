import time
import logging
from camerastreamer.camera_streamer import CameraStreamer
from communications.printer_com import Printer
from communications.arduino_com import Arduino


class AutoFocus:
    def __init__(self):
        self.camera = CameraStreamer.get_instance()
        self.printer = Printer.get_instance()
        self.arduino = Arduino.get_instance()

    def auto_focus_lap(self, samples=20):
        old_feedrate = self.printer.feedrate

        self.printer.set_feedrate(100)
        focus_values = self.get_readings_up(samples)
        max_focus = self.get_max_focus(focus_values)
        max_focus = self.auto_focus_fine()
        self.printer.zPos_focus = max_focus[0]

    def auto_focus_fine(self):
        og_focus = self.camera.get_lapacian()
        og_zPos = self.printer.zPos
        max_focus = (og_zPos, og_focus)
        focus, max_focus = self.fine_focus(max_focus, 0.025)
        if not focus:
            # fine focus downwards
            focus, max_focus = self.fine_focus(max_focus, -0.025)
        logging.info(f"[AUTOFOCUSFINE] OG Focus at {og_zPos} value: {og_focus}")
        logging.info(f"[AUTOFOCUSFINE] Focus at {max_focus[0]} value: {max_focus[1]}")
        self.printer.set_zPos(max_focus[0])
        return max_focus

    def get_readings_up(self, n):
        focus_values = []
        self.printer.set_zPos(self.printer.lens.init_pos)
        time.sleep(1)
        old_focus = 9999
        for i in range(n):
            self.printer.move_zAxis(self.printer.lens.step_focus)
            time.sleep(1)  # movement is non blocking
            focus_val = self.camera.get_lapacian()
            focus_values.append((self.printer.zPos, focus_val))
            if focus_val > old_focus + 3:
                break
            old_focus = focus_val
        return focus_values

    def fine_focus(self, max_focus, direction):
        focus = False
        while True:
            self.printer.move_zAxis(direction)
            time.sleep(1.5)  # movement is non blocking
            focus_val = self.camera.get_lapacian()
            if focus_val > max_focus[1]:
                max_focus = (self.printer.zPos, focus_val)
                focus = True
                direction = direction - (direction / 4)
                print(f"Reducing steps to {direction}")
            else:
                self.printer.move_zAxis(-direction)
                time.sleep(0.5)  # movement is non blocking
                break
        return focus, max_focus

    def get_max_focus(self, focus_values):
        # return max from a list of tuples (zPos, laplacian value)
        max_focus = (0, 0)
        for focus in focus_values:
            if focus[1] > max_focus[1]:
                max_focus = focus
        max_focus = (float(format(max_focus[0], ".2f")), max_focus[1])
        self.printer.set_zPos(max_focus[0])
        time.sleep(2)
        return max_focus
