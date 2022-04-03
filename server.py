#!/usr/bin/env python
import socket
import time
import os
import sys
import logging
import argparse
import serial
import serial.tools.list_ports
from flask import (
    Flask,
    render_template,
    Response,
    make_response,
    request,
    jsonify,
    send_file,
)
from flask_restful import Api
from camerastreamer.camera_streamer import CameraStreamer
from camerastreamer.focus_stack import FocusStack
from camerastreamer.filter import Filter
from camerastreamer.auto_focus import AutoFocus
from camerastreamer.stitcher import Stitcher
from camerastreamer.lens import LensFactory
from communications.printer_com import Printer
from communications.arduino_com import Arduino
from inference.inference import Inference
from api.camera_settings import CameraSettings, CameraAutoFocus
from api.led import Leds
from api.stepper_motors import Steppers, StepperHome, StepperCenter, StepperChangeLens


API_ROOT = "/api/v1"
DEFAULT_PORT = 5000
# os.chdir("/home/pi/Visilab/MicroHikari3D-Server")


def new_server(address):
    """Factory"""
    address = urllib.parse.urlsplit(address)
    server = Process(
        target=_FLASK_APP_.run,
        kwargs={
            "host": address.hostname,
            "port": address.port,
            # Flask cannot run in a thread with debug mode enabled:
            # https://stackoverflow.com/a/31265602/1062435
            "debug": False,
        },
    )
    return server


_FLASK_APP_ = Flask(__name__.split(".")[0])
_FLASK_API_ = Api(_FLASK_APP_)


@_FLASK_APP_.route("/")
def index():
    # Video streaming home page.
    # This should serve up your Raspberry Pi Camera video.
    return render_template("pi_home.html")


def gen(camera):
    # Video streaming generator function.  For more on generator functions see Miguel Gringberg's beautiful post here:  https://blog.miguelgrinberg.com/post/video-streaming-with-flask
    # Stream will remain open until the connection is closed
    while True:
        frame = camera.get_frame()
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


@_FLASK_APP_.route("/video_feed.mjpeg", methods=["GET"])
def video_feed():
    # Video streaming route. Put this in the src attribute of an img tag.
    return Response(
        gen(CameraStreamer.get_instance()),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@_FLASK_APP_.route("/photo.jpg", methods=["GET"])
def photo():
    args = request.args
    try:
        filter_option = args.get("filter", None)
    except:
        return 400
    if filter_option is None or filter_option == "none":
        camera = CameraStreamer.get_instance()
        photo = camera.get_photo()
    else:
        filter = Filter()
        photo = filter.filter(filter_option)
    if photo is None:
        return 400
    return send_file(photo, mimetype="image/JPEG")


@_FLASK_APP_.route("/focusstackphoto.jpg", methods=["GET"])
def focus_stack_photo():
    args = request.args
    n_focus = 3
    step = 0.02
    try:
        n_focus = int(args.get("nfocus", 3))
        step = float(args.get("step", 0.02))
        filter_option = args.get("filter", None)
    except:
        return "Bad args", 400
    if filter_option is None or filter_option == "none":
        focus_stack = FocusStack()
        photo = focus_stack.get_focus_stack_img(n_focus,step)
    else:
        filter = Filter()
        photo = filter.filter_fs(filter_option, n_focus)
    if photo is None:
        return "Bad args", 400
    return send_file(photo, mimetype="image/JPEG")


@_FLASK_APP_.route("/autofocus", methods=["GET"])
def autofocus():
    args = request.args
    auto_focuser = AutoFocus()
    if "fine" in args:
        auto_focuser.auto_focus_fine()
    else:
        auto_focuser.auto_focus_lap()
    return "OK", 200


@_FLASK_APP_.route("/inference", methods=["GET"])
def inference():
    args = request.args
    if "model" in args:
        model_name = args.get("model")
        inference = Inference(model_name)
        if inference.interpreter is None:
            return "Model does not exist", 400
        results = inference.inference()
    else:
        return jsonify(Inference.get_models())
    return jsonify(results)


@_FLASK_APP_.route("/stitch", methods=["GET"])
def stitch():
    args = request.args
    fov_x = 3
    fov_y = 3
    step_per_fov = 0.8
    focus_stack = False
    pattern = 0
    try:
        fov_x = int(args.get("fovx", 3))
        fov_y = int(args.get("fovy", 3))
        step_per_fov = float(args.get("step", 0.8))
        focus_stack = bool(args.get("focusstack", False))
        pattern = int(args.get("pattern", 0))
    except:
        return "BAD QUERY", 400
    stitcher = Stitcher(fov_x, fov_y, step_per_fov)
    if focus_stack == True:
        print('FS-Stitch')
        file_path = stitcher.focus_stack_stitch(pattern)
    else:
        file_path = stitcher.stitch(pattern)

    if file_path == "error":
        return "Server error", 500
    return send_file(file_path, mimetype="image/JPEG")


def get_internet_ip():
    # hacky solution
    print()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("1.1.1.1", 80))
    return s.getsockname()[0]


def init_communications(lens):
    port_candidates = serial.tools.list_ports.comports()
    printer_ok = False
    arduino_ok = False
    for port in port_candidates:
        if "ttyUSB" in port.name[:-1]:
            candidate = f"/dev/{port.name}"
            logging.info(
                f"[\033[92mINITCOM\033[0m] Trying to connect to {candidate} ..."
            )
            ser = serial.Serial(candidate, 115200, timeout=2)
            time.sleep(2)
            ser.write(b"M117 Server booting... \r\n")
            response = ser.readline().decode()
            logging.info(f"[\033[92mINITCOM\033[0m] Response: {response[:-1]}")
            if "echo:start" in response or "ok" in response:
                ser.close()
                logging.info("[\033[92mINITCOM\033[0m] Printer Found")
                printer = Printer.get_instance(candidate)
                time.sleep(2)
                printer.print_display(get_internet_ip())
                lens_factory = LensFactory()
                printer.lens = lens_factory.create_lens(lens)
                logging.info("[\033[92mINITCOM\033[0m] Printer Ready")
                printer_ok = True
            if "Unknown" in response:
                logging.info("[\033[92mINITCOM\033[0m] Arduino Found")
                ser.close()
                Arduino.get_instance(candidate)
                logging.info("[\033[92mINITCOM\033[0m] Arduino Ready")
                arduino_ok = True
    if not arduino_ok:
        logging.info("[\033[92mINITCOM\033[0m] Arduino not found check connection")
        sys.exit()
    if not printer_ok:
        logging.info("[\033[92mINITCOM\033[0m] Printer not found check connection")
        sys.exit()


# Setup Api Resource
_FLASK_API_.add_resource(CameraSettings, f"{API_ROOT}/camera")
_FLASK_API_.add_resource(CameraAutoFocus, f"{API_ROOT}/camera/autofocus")
_FLASK_API_.add_resource(Steppers, f"{API_ROOT}/steppers")
_FLASK_API_.add_resource(StepperHome, f"{API_ROOT}/steppers/home")
_FLASK_API_.add_resource(StepperCenter, f"{API_ROOT}/steppers/center")
_FLASK_API_.add_resource(StepperChangeLens, f"{API_ROOT}/steppers/changelens")
_FLASK_API_.add_resource(Leds, f"{API_ROOT}/leds")


if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser(description="MicroHikari3D Server")
    parser.add_argument(
        "-l", "--lens", action="store", type=float, help="default Lens", default=20
    )
    args = parser.parse_args()
    lens = args.lens

    logging.basicConfig(
        format="%(asctime)s %(message)s", stream=sys.stdout, level=logging.INFO
    )
    init_communications(lens)
    _FLASK_APP_.run(host="0.0.0.0", port=DEFAULT_PORT, debug=False, threaded=True)

    # _FLASK_APP_.run(host='0.0.0.0', port=DEFAULT_PORT, debug=True,threaded=True, ssl_context=('ssl/cert.pem', 'ssl/key.pem'))
