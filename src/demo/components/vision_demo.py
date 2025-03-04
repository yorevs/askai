from askai.core.engine.ai_vision import AIVision
from askai.core.router.tools import vision
from askai.core.router.tools.vision import offline_captioner
from askai.core.support.shared_instances import shared
from utils import init_context

import os

if __name__ == "__main__":
    init_context("vision-demo")
    vision: AIVision = shared.engine.vision()
    load_dir: str = "/Users/hjunior/Library/CloudStorage/Dropbox/Media"
    image_file: str = "eu-edvaldo-suecia.jpg"
    result = vision.caption(image_file, load_dir)
    print(result)
    # result2 = offline_captioner(os.path.join(load_dir, image_file))
    # print(result2)
