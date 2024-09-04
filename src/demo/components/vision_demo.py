from askai.core.engine.ai_vision import AIVision
from askai.core.support.shared_instances import shared

from utils import init_context

if __name__ == '__main__':
    init_context("vision-demo")
    vision: AIVision = shared.engine.vision()
    load_dir: str = "${HOME}/.config/hhs/askai/cache/pictures/photos"
    image_file: str = "eu-edvaldo-suecia.jpg"
    result = vision.caption(image_file, load_dir)
    print(result)
