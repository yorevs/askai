from PIL import Image
from transformers import AutoTokenizer, VisionEncoderDecoderModel, ViTImageProcessor

import os
import torch


class Captioner:

    def __init__(self):
        self.model = VisionEncoderDecoderModel.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
        self.feature_extractor = ViTImageProcessor.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
        self.tokenizer = AutoTokenizer.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        max_length = 16
        num_beams = 4
        self.gen_kwargs = {"max_length": max_length, "num_beams": num_beams}

        self.pic_dir = "/Users/hjunior/.config/hhs/askai/cache/pictures"

    def predict_step(self, image_paths: list[str]) -> list[str]:
        images = []
        for image_path in image_paths:
            i_image = Image.open(os.path.join(c.pic_dir, image_path))
            if i_image.mode != "RGB":
                i_image = i_image.convert(mode="RGB")
            images.append(i_image)
        pixel_values = self.feature_extractor(images=images, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(self.device)
        output_ids = self.model.generate(pixel_values, **self.gen_kwargs)
        preds = self.tokenizer.batch_decode(output_ids, skip_special_tokens=True)
        preds = [pred.strip() for pred in preds]
        return preds


if __name__ == "__main__":
    c = Captioner()
    print(c.predict_step(["photos/webcam_photo.jpg-PHOTO.jpg"]))
