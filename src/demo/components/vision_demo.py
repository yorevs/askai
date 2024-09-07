from askai.core.features.router.tools.vision import offline_captioner

import os

if __name__ == "__main__":
    # init_context("vision-demo")
    # vision: AIVision = shared.engine.vision()
    load_dir: str = "${HOME}/.config/hhs/askai/cache/pictures/photos"
    image_file: str = "eu-edvaldo-suecia.jpg"
    # result = vision.caption(image_file, load_dir)
    # print(result)
    result2 = offline_captioner(os.path.join(load_dir, image_file))
    print(result2)
