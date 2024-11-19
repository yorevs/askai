#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: demo.components
      @file: webcam-demo.py
   @created: Fri, 14 Auf 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.router.tools.webcam import *
from hspylib.core.tools.commons import sysout
from utils import init_context

if __name__ == "__main__":
    init_context("webcam-demo")
    sysout("-=" * 40)
    sysout("AskAI WebCam Demo")
    sysout("-=" * 40)
    info: str = webcam_capturer("hugo", True, "Is the person happy?")
    # info: str = webcam_identifier()
    sysout(info, markdown=True)
