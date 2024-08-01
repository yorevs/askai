#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai
      @file: __classpath__.py
   @created: Fri, 5 Jan 2024
    @author: "<B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: "https://github.com/yorevs/hspylib")
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import json
from pathlib import Path

import dotenv

from askai.core.model.api_keys import ApiKeys
from hspylib.core.metaclass.classpath import Classpath
from hspylib.core.tools.commons import get_path, run_dir

import logging as log
import os
import pydantic
import sys

if not os.environ.get("USER_AGENT"):
    # The AskAI User Agent, required by the langchain framework
    ASKAI_USER_AGENT: str = "AskAI-User-Agent"
    os.environ["USER_AGENT"] = ASKAI_USER_AGENT


try:
    keys: ApiKeys = ApiKeys()
except pydantic.v1.error_wrappers.ValidationError as err:
    if not ApiKeys.prompt():
        log.error(err.json())
        sys.exit(127)


class _Classpath(Classpath):
    """TODO"""

    def __init__(self):
        super().__init__(get_path(__file__), get_path(run_dir()), (get_path(__file__) / "resources"))


# Instantiate the classpath singleton
assert (classpath := _Classpath().INSTANCE) is not None, "Failed to create Classpath instance"
