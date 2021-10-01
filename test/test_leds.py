#!/usr/bin/env/python3

import unittest
import json
import requests

SERVER_ADDRESS = "http://localhost:5000"
SERVER_API_URI = f"{SERVER_ADDRESS}/api/v1"


class TestLed(unittest.TestCase):
    def change_value(self, choices, value_str):
        try:
            for new_value in choices:
                new_data = {f"{value_str}": new_value}
                result = requests.put(f"{SERVER_API_URI}/leds", json=new_data)
                self.assertEqual(result.status_code, 200)
                result = json.loads(result.content)
        except Exception as error:
            raise error

    """Led test"""

    def test_change_bottom_light(self):
        try:
            choices = [True, False]
            self.change_value(choices, "bottom_light")
        except Exception as error:
            raise error

    def test_change_rgbw_red(self):
        try:
            choices = [0, 128, 254]
            self.change_value(choices, "rgbw_red")
        except Exception as error:
            raise error

    def test_change_rgbw_green(self):
        try:
            choices = [0, 128, 254]
            self.change_value(choices, "rgbw_green")
        except Exception as error:
            raise error

    def test_change_rgbw_blue(self):
        try:
            choices = [0, 128, 254]
            self.change_value(choices, "rgbw_blue")
        except Exception as error:
            raise error

    def test_change_rgbw_white(self):
        try:
            choices = [0, 128, 254]
            self.change_value(choices, "rgbw_white")
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

    def test_change_bad_bottom_light(self):
        try:
            choices = [-10, 300, "test", 0.3]
            self.change_bad_value(choices, "bottom_light")
        except Exception as error:
            raise error

    def test_change_bad_rgbw_red(self):
        try:
            choices = [-10, 300, True, "test", 0.3]
            self.change_bad_value(choices, "rgbw_red")
        except Exception as error:
            raise error

    def test_change_bad_rgbw_green(self):
        try:
            choices = [-10, 300, True, "test", 0.3]
            self.change_bad_value(choices, "rgbw_green")
        except Exception as error:
            raise error

    def test_change_bad_rgbw_blue(self):
        try:
            choices = [-10, 300, True, "test"]
            self.change_bad_value(choices, "rgbw_blue")
        except Exception as error:
            raise error

    def test_change_bad_rgbw_white(self):
        try:
            choices = [-10, 300, True, "test", 0.3]
            self.change_bad_value(choices, "rgbw_white")
        except Exception as error:
            raise error


if __name__ == "__main__":
    unittest.main()
