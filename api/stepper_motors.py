import serial
import time
from flask_restful import Resource, Api, reqparse
from communications.printer_com import Printer
from camerastreamer.lens import LensFactory


class Steppers(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("xPos", type=float, location="json")
    parser.add_argument("yPos", type=float, location="json")
    parser.add_argument("zPos", type=float, location="json")
    parser.add_argument("xAxis", type=float, location="json")
    parser.add_argument("yAxis", type=float, location="json")
    parser.add_argument("zAxis", type=float, location="json")
    parser.add_argument("feedrate", type=float, location="json")

    def make_response(self):
        printer = Printer.get_instance()
        response = {
            "xPos": printer.xPos,
            "yPos": printer.yPos,
            "zPos": printer.zPos,
            "feedrate": printer.feedrate,
        }
        return response

    def get(self):
        return self.make_response(), 200

    def put(self):
        args = self.parser.parse_args(strict=True)
        printer = Printer.get_instance()
        if args["feedrate"] is not None:
            if args["feedrate"] <= 3000.0 and args["feedrate"] >= 100.0:
                printer.set_feedrate(args["feedrate"])
            else:
                return 400
        if args["xPos"] is not None:
            if args["xPos"] <= 100.0 and args["xPos"] > 5.0:
                printer.set_xPos(args["xPos"])
            else:
                return 400
        if args["yPos"] is not None:
            if args["yPos"] <= 100.0 and args["yPos"] > 5.0:
                printer.set_yPos(args["yPos"])
            else:
                return 400
        if args["zPos"] is not None:
            if args["zPos"] <= 100.0 and args["zPos"] > 0.2:
                printer.set_zPos(args["zPos"])
            else:
                return 400

        if args["xAxis"] is not None:
            printer.move_xAxis(args["xAxis"])
        if args["yAxis"] is not None:
            printer.move_yAxis(args["yAxis"])
        if args["zAxis"] is not None:
            printer.move_zAxis(args["zAxis"])
        return self.make_response(), 200


class StepperHome(Resource):
    def get(self):
        printer = Printer.get_instance()
        printer.home()
        return "OK", 200


class StepperCenter(Resource):
    def get(self):
        printer = Printer.get_instance()
        printer.center()
        return "OK", 200


class StepperChangeLens(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("magnification", type=str, location="json")

    def get(self):
        printer = Printer.get_instance()
        printer.change_lens()
        return "OK", 200

    def put(self):
        args = self.parser.parse_args(strict=True)
        printer = Printer.get_instance()
        if args["magnification"] is not None:
            print(printer.zPos_focus)
            lens_factory = LensFactory()
            lens = lens_factory.create_lens(args["magnification"])
            if lens is not None:
                printer.lens = lens
                printer.set_zPos(printer.zPos_focus)
        return "OK", 200
