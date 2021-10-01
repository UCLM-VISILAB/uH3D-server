import serial
import time
from flask_restful import Resource, Api, reqparse
from communications.arduino_com import Arduino


class Leds(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("bottom_light", type=bool, location="json")
    parser.add_argument("rgbw_red", type=int, choices=range(0, 256), location="json")
    parser.add_argument("rgbw_green", type=int, choices=range(0, 256), location="json")
    parser.add_argument("rgbw_blue", type=int, choices=range(0, 256), location="json")
    parser.add_argument("rgbw_white", type=int, choices=range(0, 256), location="json")
    parser.add_argument("rgbw_light", type=int, choices=range(0, 12), location="json")

    def make_response(self):
        arduino = Arduino.get_instance()
        response = {
            "bottom_light": arduino.bottom_light,
            "rgbw_ring": arduino.rgbw_ring,
        }
        return response

    def get(self):
        return self.make_response(), 200

    def put(self):
        arduino = Arduino.get_instance()
        args = self.parser.parse_args(strict=True)
        if args["bottom_light"] is not None:
            if args["bottom_light"]:
                arduino.bottom_lights_on()
            else:
                arduino.bottom_lights_off()
        if (
            args["rgbw_red"] is not None
            and args["rgbw_green"] is not None
            and args["rgbw_blue"] is not None
            and args["rgbw_white"] is not None
        ):
            if args["rgbw_light"] is not None:
                arduino.set_rgbw_light(
                    args["rgbw_red"],
                    args["rgbw_green"],
                    args["rgbw_blue"],
                    args["rgbw_white"],
                    args["rgbw_light"],
                )
            else:
                arduino.set_rgbw_ring(
                    args["rgbw_red"],
                    args["rgbw_green"],
                    args["rgbw_blue"],
                    args["rgbw_white"],
                )
        return self.make_response(), 200
