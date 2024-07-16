#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai
      @file: __classpath__.py
   @created: Fri, 5 Jan 2024
    @author: "<B>H</B>ugo <B>S</B>aporetti <B>J</B>unior")"
      @site: "https://github.com/yorevs/hspylib")
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from hspylib.core.metaclass.classpath import Classpath
from hspylib.core.tools.commons import get_path, run_dir

import os

if not os.environ.get("USER_AGENT"):
    # The AskAI User Agent, required by the langchain framework
    ASKAI_USER_AGENT: str = "AskAI-User-Agent"
    os.environ["USER_AGENT"] = ASKAI_USER_AGENT


class _Classpath(Classpath):
    """TODO"""

    def __init__(self):
        super().__init__(get_path(__file__), get_path(run_dir()), (get_path(__file__) / "resources"))


# Instantiate the classpath singleton
assert (classpath := _Classpath().INSTANCE) is not None, "Failed to create Classpath instance"
