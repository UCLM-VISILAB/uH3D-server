import time
import logging
import cv2
import os
import json


class Lens:
    def __init__(self, init_pos, step_stitch, step_focus, magnification):
        self.init_pos = init_pos
        self.step_stitch = step_stitch
        self.step_focus = step_focus
        self.magnification = magnification


class LensFactory:
    def create_lens(self, magnification):
        # reads lens.json file in ./config and creates lens objects using magnification as id
        with open("./config/lens.json", "r") as jsonfile:
            data = json.load(jsonfile)
            lens_dict = data.get(f"{magnification}")
            if lens_dict is None:
                return None
            return self._create_lens_from_dict(lens_dict, magnification)

    def _create_lens_from_dict(self, lens_dict, magnification):
        init_post = lens_dict.get("init_pos")
        step_stitch = lens_dict.get("step_stitch")
        step_focus = lens_dict.get("step_focus")
        magnification = magnification
        return Lens(init_post, step_stitch, step_focus, magnification)


class LensSerializer:
    def serialize(self, lens, format):
        if format == "JSON":
            return self._serialize_to_json(lens)
        else:
            raise ValueError(format)

    def _serialize_to_json(self, lens):
        payload = {
            "step_stitch": lens.step_stitch,
            "init_pos": lens.init_pos,
            "step_focus": lens.step_focus,
            "magnification": lens.magnification,
        }
        return json.dumps(payload)
