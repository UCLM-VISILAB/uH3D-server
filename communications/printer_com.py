import time
import serial
import logging


SERIAL_SPEED = 115200


class Printer:
    __instance__ = None

    def __init__(self, serial_port):
        if Printer.__instance__ is None:
            self.xPos = 0.0
            self.yPos = 0.0
            self.zPos = 0.0
            self.zPos_focus = 0.0
            self.feedrate = 0
            self.lens = None
            self.serial_port = serial_port
            self.mode = 0  # 0 absolute, 1 relative
            self.ser = serial.Serial(self.serial_port, SERIAL_SPEED, timeout=8)
            time.sleep(4)
            self.home()
            self.center()
            Printer.__instance__ = self
        else:
            raise Exception("There's only one 3d Printer!!")

    @staticmethod
    def get_instance(serial_port=None):
        if not Printer.__instance__:
            if serial_port is not None:
                Printer(serial_port)
        return Printer.__instance__

    def send_command(self, comm):
        logging.info(f"[\033[96mPRINTER\033[0m] Sending com: {comm[:-1]}")
        self.ser.flushInput()
        self.ser.write(comm.encode())
        response = self.ser.readline().decode()
        while "ok" not in response or "start" not in response:
            logging.info(f"[\033[94mPRINTER\033[0m] Response: {response[:-1]}")

            if "start" in response or "ok" in response:
                break
            if "Error:Printer halted" in response:
                logging.warning("\033[91mPRINTER ERROR QUITTING")
                quit()
            response = self.ser.readline().decode()
        self.ser.flushInput()
        return response

    def check_mode(self, desired_mode):
        # checks if the printer is in the correct mode and sends the correct gcode
        if desired_mode != self.mode:
            if desired_mode == 0:
                # change to absolute
                self.send_command("G90\n")
                self.mode = 0
            else:
                # change to relative
                self.send_command("G91\n")
                self.mode = 1

    def print_display(self, text):
        mess = f"M117 {text}\n"
        self.send_command(mess)

    def is_move_save(self, new_Pos):
        if new_Pos < 0 or new_Pos > 100:
            return False
        return True

    def home(self):
        self.move_zAxis(20)
        mess = "G28\n"
        response = self.send_command(mess)
        if "ok\n" in response:
            self.xPos = 0
            self.yPos = 0
            self.zPos = 0
            self.did_home = True
            logging.info(f"[\033[96mPRINTER\033[0m] Home ok")
        return response

    def set_xPos(self, pos):
        mess = f"G1 X{pos}\n"
        self.check_mode(0)
        response = self.send_command(mess)
        if "ok\n" in response:
            logging.info(f"[\033[96mPRINTER\033[0m] xAxis to pos: {pos}")
            self.xPos = pos
        return response

    def set_yPos(self, pos):
        mess = f"G1 Y{pos}\n"
        self.check_mode(0)
        response = self.send_command(mess)
        if "ok\n" in response:
            logging.info(f"[\033[96mPRINTER\033[0m] yAxis to pos: {pos}")
            self.yPos = pos
        return response

    def set_zPos(self, pos):
        if self.is_move_save(pos):
            mess = f"G1 Z{pos}\n"
            self.check_mode(0)
            response = self.send_command(mess)
            if "ok\n" in response:
                logging.info(f"[\033[96mPRINTER\033[0m] zAxis to pos: {pos}")
                self.zPos = pos
        else:
            logging.warning("That was not save, not moving anywhere :(")
        return response

    def set_feedrate(self, feedrate):
        mess = f"G0 F{feedrate}\n"
        response = self.send_command(mess)
        if "ok\n" in response:
            logging.info(f"[\033[96mPRINTER\033[0m] Feedrate changed to: {feedrate}")
            self.feedrate = feedrate
        response

    def move_xAxis(self, cor):
        mess = f"G0 X{cor}\n"
        self.check_mode(1)
        response = self.send_command(mess)
        if "ok\n" in response:
            logging.info(f"[\033[96mPRINTER\033[0m] xAxis cor: {cor}")
            self.xPos += cor

    def move_yAxis(self, cor):
        mess = f"G0 Y{cor}\n"
        self.check_mode(1)
        response = self.send_command(mess)
        if "ok\n" in response:
            logging.info(f"[\033[96mPRINTER\033[0m] yAxis cor: {cor}")
            self.yPos += cor

    def move_zAxis(self, cor):
        if self.is_move_save(self.zPos + cor):
            mess = f"G0 Z{cor}\n"
            self.check_mode(1)
            response = self.send_command(mess)
            if "ok\n" in response:
                logging.info(f"[\033[96mPRINTER\033[0m] zAxis cor: {cor}")
                self.zPos += cor
        else:
            logging.warning("That move was not save :(")

    def center(self):
        self.set_zPos(3)
        self.set_feedrate(3000)
        self.set_zPos(20)
        self.set_yPos(104)
        self.set_xPos(69)
        self.set_zPos(3.2)
        self.set_feedrate(1000)
        time.sleep(10)
        logging.info("[\033[96mPRINTER\033[0m] Center OK")

    def change_lens(self):
        old_feedrate = self.feedrate
        self.set_feedrate(3000)
        self.set_zPos(20)
        self.set_feedrate(old_feedrate)
        logging.info("[\033[96mPRINTER\033[0m] Change Lens OK")
