import time
import serial
import logging

SERIAL_SPEED = 115200


class Arduino:
    __instance__ = None

    def __init__(self, serial_port):
        if Arduino.__instance__ is None:
            self.serial_port = serial_port
            self.bottom_light = False
            self.rgbw_ring = [0, 0, 0, 255]
            self.ser = serial.Serial(self.serial_port, SERIAL_SPEED)
            time.sleep(5)  # new serial connection makes the printer resets it self
            Arduino.__instance__ = self
        else:
            raise Exception("There's only one Arduino!!")

    @staticmethod
    def get_instance(serial_port=None):
        if not Arduino.__instance__:
            if serial_port is not None:
                Arduino(serial_port)
        return Arduino.__instance__

    def send_command(self, comm):
        logging.info(f"[Arduino] Sending com: {comm[:-1]}")
        self.ser.write(comm.encode())
        response = self.ser.readline().decode()
        logging.info(f"[Arduino] Response: {response[:-1]}")

    def bottom_lights_on(self):
        self.send_command("L012 1\n")
        logging.info("[Arduino] Bottom Light ON")
        self.bottom_light = True

    def bottom_lights_off(self):
        self.send_command("L012 0\n")
        logging.info("[Arduino] Bottom Light OFF")
        self.bottom_light = False

    def set_rgbw_ring(self, red, green, blue, white):
        # L008 Rxxx Gxxx Bxxx Wxxx
        comm = f"R{str(red).zfill(3)} G{str(green).zfill(3)} B{str(blue).zfill(3)} W{str(white).zfill(3)}"
        self.send_command(f"L008 {comm}\n")
        logging.info(f"[Arduino] RGBW Lights: {comm}")
        for light in range(len(self.rgbw_ring)):
            self.rgbw_ring[light] = [red, green, blue, white]

    def set_rgbw_light(self, red, green, blue, white, light):
        # L008 Rxxx Gxxx Bxxx Wxxx Lxx
        comm = f"R{str(red).zfill(3)} G{str(green).zfill(3)} B{str(blue).zfill(3)} W{str(white).zfill(3)} L {str(light).zfill(2)}"
        self.send_command(f"L008 {comm}\n")
        logging.info(f"[Arduino]: RGBW Light: {comm}")
        self.rgbw_ring[light] = [red, green, blue, white]
