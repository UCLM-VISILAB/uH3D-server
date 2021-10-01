import logging
from flask_restful import Resource, Api, reqparse
from camerastreamer.camera_streamer import CameraStreamer
from camerastreamer.auto_focus import AutoFocus


class CameraSettings(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument(
        "photo_resolution",
        type=tuple,
        choices=[(4056, 3040), (3280, 2464)],
        location="json",
    )
    parser.add_argument(
        "stream_resolution",
        type=tuple,
        choices=[(640, 480), (1280, 960), (1640, 1232)],
        location="json",
    )
    parser.add_argument(
        "rotation", type=int, choices=[0, 90, 180, 270], location="json"
    )
    parser.add_argument(
        "iso",
        type=int,
        choices=[0, 100, 200, 320, 400, 500, 600, 640, 800],
        location="json",
    )
    parser.add_argument(
        "sharpness", type=int, choices=range(-100, 101), location="json"
    )
    parser.add_argument(
        "exposure_compensation", type=int, choices=range(-25, 26), location="json"
    )
    parser.add_argument(
        "exposure_mode",
        type=str,
        choices=["off", "auto", "night", "backlight"],
        location="json",
    )
    parser.add_argument("shutter_speed", type=float, location="json")
    parser.add_argument("image_denoise", type=bool, location="json")
    parser.add_argument(
        "saturation", type=int, choices=range(-100, 101), location="json"
    )
    parser.add_argument("zoom", type=tuple, location="json")
    parser.add_argument(
        "awb_mode",
        type=str,
        choices=["off", "auto", "sunlight", "shade"],
        location="json",
    )
    # parser.add_argument('awb_gains', type=float, choices=[(range(0.0,8.0),range(0.0,8.0))], location='json')

    def make_response(self):
        camerastreamer = CameraStreamer.get_instance()
        values = {
            "photo_resolution": camerastreamer.photo_resolution,
            "stream_resolution": camerastreamer.stream_resolution,
            "rotation": camerastreamer.camera.rotation,
            "iso": camerastreamer.camera.iso,
            "sharpness": camerastreamer.camera.sharpness,
            "exposure_compensation": camerastreamer.camera.exposure_compensation,
            "exposure_mode": camerastreamer.camera.exposure_mode,
            "shutter_speed": camerastreamer.camera.shutter_speed,
            "image_denoise": camerastreamer.camera.image_denoise,
            "saturation": camerastreamer.camera.saturation,
            "zoom": camerastreamer.camera.zoom,
            "awb_mode": camerastreamer.camera.awb_mode,
            "awb_gains": str(camerastreamer.camera.awb_gains),
        }
        return values

    def get(self):
        return self.make_response(), 200

    def put(self):
        args = self.parser.parse_args(strict=True)
        camerastreamer = CameraStreamer.get_instance()
        if args["photo_resolution"] is not None:
            camerastreamer.photo_resolution = args["photo_resolution"]
        if args["stream_resolution"] is not None:
            camerastreamer.change_stream_resolution(args["stream_resolution"])
        if args["rotation"] is not None:
            camerastreamer.camera.rotation = args["rotation"]
        if args["iso"] is not None:
            camerastreamer.camera.iso = args["iso"]
        if args["sharpness"] is not None:
            camerastreamer.camera.sharpness = args["sharpness"]
        if args["exposure_compensation"] is not None:
            camerastreamer.camera.exposure_compensation = args["exposure_compensation"]
        if args["exposure_mode"] is not None:
            camerastreamer.camera.exposure_mode = args["exposure_mode"]
        if args["shutter_speed"] is not None:
            camerastreamer.camera.shutter_speed = args["shutter_speed"]
        if args["image_denoise"] is not None:
            camerastreamer.camera.image_denoise = args["image_denoise"]
        if args["saturation"] is not None:
            camerastreamer.camera.saturation = args["saturation"]
        if args["zoom"] is not None:
            camerastreamer.camera.zoom = args["zoom"]
        return self.make_response(), 200


class CameraAutoFocus(Resource):
    def get(self):
        try:
            auto_focuser = AutoFocus()
            auto_focuser.auto_focus_lap()
            return "OK", 200
        except Exception as e:
            logging.warning(f"Exception {e}")
