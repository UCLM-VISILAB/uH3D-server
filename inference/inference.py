import numpy as np
import io
import os
import json
import time
import logging
from camerastreamer.camera_streamer import CameraStreamer
from PIL import Image
from tflite_runtime.interpreter import Interpreter


class Inference:
    def __init__(self, model_name):
        logging.info(f"[INFERENCE] Start with model: {model_name}")
        self.interpreter, self.labels = self._load_model_json(model_name)
        logging.info(f"[INFERENCE] Model {model_name} loaded")
        self.camera = CameraStreamer.get_instance()

    def _load_model_json(self, model_name):
        with open("./inference/models.json", "r") as jsonfile:
            data = json.load(jsonfile)
            model_dict = data.get(f"{model_name}")
            if model_dict is None:
                return None, None
            return Interpreter(model_dict["path"]), model_dict["labels"]

    def _set_input_tensor(self, image):
        tensor_index = self.interpreter.get_input_details()[0]["index"]
        input_tensor = self.interpreter.tensor(tensor_index)()[0]
        input_tensor[:, :] = image

    def _classify_image(self, image, top_k=1):
        top_k = len(self.labels) - 1
        self._set_input_tensor(image)
        self.interpreter.invoke()
        output_details = self.interpreter.get_output_details()[0]
        output = np.squeeze(self.interpreter.get_tensor(output_details["index"]))

        if output_details["dtype"] == np.uint8:
            scale, zero_point = output_details["quantization"]
            output = scale * (output - zero_point)
        return output

    def label_results(self, results):
        output = []
        for i in range(0, len(self.labels)):
            output.append([self.labels[i], results[i]])
        return output

    def inference(self):
        self.interpreter.allocate_tensors()
        _, height, width, _ = self.interpreter.get_input_details()[0]["shape"]
        sample = self.camera.get_photo()
        image = (
            Image.open(sample).convert("RGB").resize((width, height), Image.ANTIALIAS)
        )
        logging.info(f"[INFERENCE] Image converted to input size")
        start_time = time.time()
        results = self._classify_image(image)
        labeled_results = self.label_results(results)
        elapsed_ms = (time.time() - start_time) * 1000
        logging.info(f"[INFERENCE] Done total time: {elapsed_ms} ms")
        return labeled_results

    def get_models():
        models = {"models": []}
        with open("./inference/models.json", "r") as jsonfile:
            data = json.load(jsonfile)
            for model in data:
                models["models"].append(model)
        return models
