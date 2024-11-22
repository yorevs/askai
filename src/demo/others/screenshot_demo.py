from askai.core.router.tools.vision import capture_screenshot
from hspylib.core.tools.commons import sysout
from utils import init_context

if __name__ == "__main__":
    init_context("camera-demo")
    sysout(capture_screenshot("gabiroba.jpeg"))
