from askai.core.features.router.tools.vision import take_screenshot
from hspylib.core.tools.commons import sysout

from utils import init_context

if __name__ == "__main__":
    init_context("camera-demo")
    sysout(take_screenshot("gabiroba.jpeg"))
