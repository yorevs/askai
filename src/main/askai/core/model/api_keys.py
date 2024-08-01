#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.askai_configs
      @file: askai_configs.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import os
from pathlib import Path

from hspylib.core.enums.charset import Charset
from pydantic.v1 import BaseSettings


class ApiKeys(BaseSettings):
    """TODO"""

    OPENAI_API_KEY: str
    GOOGLE_API_KEY: str
    DEEPL_API_KEY: str

    class Config:
        env_file = str(os.path.join(Path.home(), ".env"))
        env_file_encoding = Charset.UTF_8.val
