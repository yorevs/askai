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
import dotenv
from clitt.core.tui.minput.input_validator import InputValidator
from clitt.core.tui.minput.menu_input import MenuInput
from clitt.core.tui.minput.minput import minput
from hspylib.core.enums.charset import Charset
from pathlib import Path

from pydantic.v1 import Field, BaseSettings, validator

import os

API_KEY_FILE: str = os.environ.get("HHS_ENV_FILE", str(os.path.join(Path.home(), ".env")))

dotenv.load_dotenv(API_KEY_FILE)


class ApiKeys(BaseSettings):
    """Provide a class no handle the required Api Keys."""

    OPENAI_API_KEY: str = Field(..., description="Open AI Api Key")
    GOOGLE_API_KEY: str = Field(..., description="Google Api Key")
    DEEPL_API_KEY: str = Field(..., description="DeepL Api Key")

    @validator('OPENAI_API_KEY', 'GOOGLE_API_KEY', 'DEEPL_API_KEY')
    def not_empty(cls, value):
        if not value or not value.strip():
            raise ValueError('must not be empty or blank')
        return value

    class Config:
        env_file = API_KEY_FILE
        env_file_encoding = Charset.UTF_8.val

    @staticmethod
    def prompt() -> bool:
        """TODO"""

        # fmt: off
        form_fields = MenuInput.builder() \
            .field() \
                .label('OPENAI_API_KEY') \
                .value(os.environ.get("OPENAI_API_KEY")) \
                .min_max_length(51, 51) \
                .validator(InputValidator.anything()) \
                .build() \
            .field() \
                .label('GOOGLE_API_KEY') \
                .value(os.environ.get("GOOGLE_API_KEY")) \
                .min_max_length(39, 39) \
                .validator(InputValidator.anything()) \
                .build() \
            .field() \
                .label('DEEPL_API_KEY') \
                .value(os.environ.get("DEEPL_API_KEY")) \
                .min_max_length(39, 39) \
                .validator(InputValidator.anything()) \
                .build() \
            .build()
        # fmt: on

        if result := minput(form_fields, "Please fill all required Api Keys"):
            with open(API_KEY_FILE, 'r+', encoding=Charset.UTF_8.val) as f_envs:
                envs = f_envs.readlines()
            with open(API_KEY_FILE, 'w', encoding=Charset.UTF_8.val) as f_envs:
                all_envs: set[str] = set(map(str.strip, envs))
                for key, value in zip(result.attributes, result.values):
                    os.environ[key.upper()] = value
                    all_envs.add(f"export {key.upper()}={value}")
                final_envs: list[str] = list(all_envs)
                final_envs.sort()
                f_envs.write(os.linesep.join(final_envs))
            return True

        return False
