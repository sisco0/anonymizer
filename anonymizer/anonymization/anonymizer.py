import json
from pathlib import Path

import numpy as np
from PIL import Image
from tqdm import tqdm

from anonymizer.utils import Box


def load_np_image(image_path):
    image = Image.open(image_path).convert('RGB')
    np_image = np.array(image)
    return np_image


def save_np_image(image, image_path):
    pil_image = Image.fromarray((image).astype(np.uint8), mode='RGB')
    pil_image.save(image_path)


def save_detections(detections, detections_path):
    json_output = []
    for box in detections:
        json_output.append({
            'y_min': box.y_min,
            'x_min': box.x_min,
            'y_max': box.y_max,
            'x_max': box.x_max,
            'score': box.score,
            'kind': box.kind
        })
    with open(detections_path, 'w') as output_file:
        json.dump(json_output, output_file, indent=2)


class Anonymizer:
    def __init__(self, detectors, obfuscator):
        self.detectors = detectors
        self.obfuscator = obfuscator

    def anonymize_image(self, image, detection_thresholds, cubemap=False):
        assert set(self.detectors.keys()) == set(detection_thresholds.keys()),\
            'Detector names must match detection threshold names'
        detected_boxes = []
        if cubemap:
            w, h, _ = np.shape(image)
            # Split cubemap into pieces
            piecesRects = [
                [0, 0, w/3, h], # Large front face
                [w/3, 0, 2*w/3, h/2], # Back face
                [2*w/3, 0, w, h/2], # Top face (Superman!)
                [w/3, h/2, 2*w/3, h], # Right face
                [2*w/3, h/2, w, h] # Left face
            ]
            for idx, rect in enumerate(piecesRects):
                print(np.shape(image))
                piece = image[round(rect[1]):round(rect[3]), round(rect[0]):round(rect[2])]
                obfuscated_piece, piece_detected_boxes = self.anonymize_image(piece, detection_thresholds, False)
                print(piece_detected_boxes)
                import pdb; pdb.set_trace();
                detected_boxes = detected_boxes + [box + Box(rect[1], rect[0], rect[1], rect[0], 0.0, "face")
                        for box in piece_detected_boxes]
            # TODO Remove this and change!
            return self.obfuscator.obfuscate(image, detected_boxes), detected_boxes
        else:
            for kind, detector in self.detectors.items():
                new_boxes = detector.detect(image, detection_threshold=detection_thresholds[kind])
                detected_boxes.extend(new_boxes)
            return self.obfuscator.obfuscate(image, detected_boxes), detected_boxes

    def anonymize_images(self, input_path, output_path, detection_thresholds, file_types, write_json, cubemap):
        print(f'Anonymizing images in {input_path} and saving the anonymized images to {output_path}...')

        Path(output_path).mkdir(exist_ok=True)
        assert Path(output_path).is_dir(), 'Output path must be a directory'

        files = []
        for file_type in file_types:
            files.extend(list(Path(input_path).glob(f'**/*.{file_type}')))

        for input_image_path in tqdm(files):
            # Create output directory
            relative_path = input_image_path.relative_to(input_path)
            (Path(output_path) / relative_path.parent).mkdir(exist_ok=True, parents=True)
            output_image_path = Path(output_path) / relative_path
            output_detections_path = (Path(output_path) / relative_path).with_suffix('.json')

            # Anonymize image
            image = load_np_image(str(input_image_path))
            anonymized_image, detections = self.anonymize_image(image=image, detection_thresholds=detection_thresholds, cubemap=cubemap)
            save_np_image(image=anonymized_image, image_path=str(output_image_path))
            if write_json:
                save_detections(detections=detections, detections_path=str(output_detections_path))
