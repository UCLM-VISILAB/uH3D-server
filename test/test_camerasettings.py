#!/usr/bin/env/python3

import unittest
import json
import requests

SERVER_ADDRESS = "http://localhost:5000"
SERVER_API_URI = f"{SERVER_ADDRESS}/api/v1"


class TestCameraSettings(unittest.TestCase):
    def change_value(self, choices, value_str):
        try:
            for new_value in choices:
                new_data = {f"{value_str}": new_value}
                result = requests.put(f"{SERVER_API_URI}/camera", json=new_data)
                self.assertEqual(result.status_code, 200)
                result = json.loads(result.content)
                self.assertEqual(new_data[value_str], result[value_str])
        except Exception as error:
            raise error

    """Camera setting test"""

    def test_change_rotation(self):
        try:
            choices = [0, 90, 180, 270]
            self.change_value(choices, "rotation")
        except Exception as error:
            raise error

    def test_change_iso(self):
        try:
            choices = [0, 100, 200, 320, 400, 500, 600, 640, 800]
            self.change_value(choices, "iso")
        except Exception as error:
            raise error

    def test_change_sharpness(self):
        try:
            choices = [-100, -50, 0, 50, 100]
            self.change_value(choices, "sharpness")
        except Exception as error:
            raise error

    def test_change_exposure_compensation(self):
        try:
            choices = [-25, -10, 0, 10, 25]
            self.change_value(choices, "exposure_compensation")
        except Exception as error:
            raise error

    def test_change_exposure_mode(self):
        try:
            choices = ["off", "auto", "night", "backlight"]
            self.change_value(choices, "exposure_mode")
        except Exception as error:
            raise error

    def test_change_image_denoise(self):
        try:
            choices = [True, False]
            self.change_value(choices, "image_denoise")
        except Exception as error:
            raise error

    def test_change_saturation(self):
        try:
            choices = [-100, -50, 0, 50, 100]
            self.change_value(choices, "saturation")
        except Exception as error:
            raise error

    def test_change_awb_mode(self):
        try:
            choices = ["auto", "sunlight", "shade"]
            self.change_value(choices, "awb_mode")
        except Exception as error:
            raise error

    """Test not accepted values"""

    def change_bad_value(self, choices, value_str):
        try:
            for new_value in choices:
                new_data = {f"{value_str}": new_value}
                result = requests.put(f"{SERVER_API_URI}/camera", json=new_data)
                self.assertEqual(result.status_code, 400)
                result = json.loads(result.content)
        except Exception as error:
            raise error

    def test_bad_value_rotation(self):
        try:
            choices = ["test", 3.254, -69, 7842, True]
            self.change_bad_value(choices, "rotation")
        except Exception as error:
            raise error

    def test_bad_value_iso(self):
        try:
            choices = ["test", 3.254, -69, 7842, True]
            self.change_bad_value(choices, "iso")
        except Exception as error:
            raise error

    def test_bad_value_sharpness(self):
        try:
            choices = ["test", -609, 7842, True]
            self.change_bad_value(choices, "sharpness")
        except Exception as error:
            raise error

    def test_bad_value_exposure_compensation(self):
        try:
            choices = ["test", 3.254, -609, 7842, True]
            self.change_bad_value(choices, "exposure_compensation")
        except Exception as error:
            raise error

    def test_bad_value_exposure_mode(self):
        try:
            choices = ["test", 3.254, -609, 7842, True]
            self.change_bad_value(choices, "exposure_mode")
        except Exception as error:
            raise error

    def test_bad_value_image_denoise(self):
        try:
            choices = ["test", 3.254, -609, 7842]
            self.change_bad_value(choices, "image_denoise")
        except Exception as error:
            raise error

    def test_bad_value_saturation(self):
        try:
            choices = ["test", 3.254, -609, 7842, True]
            self.change_bad_value(choices, "saturation")
        except Exception as error:
            raise error

    def test_bad_value_awb_mode(self):
        try:
            choices = ["test", 3.254, -609, 7842, True]
            self.change_bad_value(choices, "awb_mode")
        except Exception as error:
            raise error


if __name__ == "__main__":
    unittest.main()
