#!/usr/bin/env/python3

import unittest
import json
import requests

SERVER_ADDRESS = "http://localhost:5000"
SERVER_API_URI = f"{SERVER_ADDRESS}/api/v1"


class TestStepperMotors(unittest.TestCase):
    def change_value(self, choices, value_str):
        try:
            for new_value in choices:
                new_data = {f"{value_str}": new_value}
                result = requests.put(f"{SERVER_API_URI}/steppers", json=new_data)
                self.assertEqual(result.status_code, 200)
                result = json.loads(result.content)
                self.assertEqual(new_data[value_str], result[value_str])
        except Exception as error:
            raise error

    """Stepper motors test"""

    def test_zPos(self):
        choices = [50]
        self.change_value(choices, "zPos")

    def test_xPos(self):
        choices = [50]
        self.change_value(choices, "xPos")

    def test_yPos(self):
        choices = [50]
        self.change_value(choices, "yPos")

    def test_feedrate(self):
        choices = [100, 1000, 3000]
        self.change_value(choices, "feedrate")

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

    def test_bad_zPos(self):
        choices = [-5, 200, "test", False]
        self.change_bad_value(choices, "zPos")

    def test_bad_xPos(self):
        choices = [-5, 200, "test", False]
        self.change_bad_value(choices, "xPos")

    def test_bad_yPos(self):
        choices = [-5, 200, "test", False]
        self.change_bad_value(choices, "yPos")

    def test_bad_feedrate(self):
        choices = [-200, 4100, "test", False]
        self.change_bad_value(choices, "feedrate")


if __name__ == "__main__":
    unittest.main()
