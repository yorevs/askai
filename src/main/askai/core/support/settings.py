#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.support
      @file: settings.py
   @created: Tue, 23 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

import os
from typing import Any

from hspylib.core.config.properties import Properties
from hspylib.core.preconditions import check_argument
from hspylib.core.tools.commons import touch_file
from hspylib.core.tools.text_tools import ensure_endswith


class Settings(Properties):
    """The Settings class represents a persistent set of mutable settings. Each key and its corresponding value in the
    settings dictionary.Format and rules follows the properties approach."""

    def __init__(self, filename: str = None, profile: str | None = None, load_dir: str | None = None) -> None:
        _, ext = os.path.splitext(filename)
        check_argument(ext == ".properties", "Only '.properties' formatted files are permitted!")
        self._load_dir = load_dir
        self._filename = filename
        touch_file(self.filepath)
        super().__init__(filename, profile, load_dir)

    @property
    def filepath(self) -> str:
        return ensure_endswith(f"{self._load_dir}/{self._filename}", ".properties")

    def set(self, key: str, value: Any) -> None:
        """Add or set the setting and it's associated value."""
        self._properties[key] = value

    def remove(self, key: str) -> str:
        """Remove a setting specified by key."""
        return self._properties.pop(key, None)

    def clear(self) -> None:
        """Remove all settings."""
        self._properties.clear()

    def save(self) -> None:
        """Save current settings to the associated file."""
        with open(self.filepath, "w") as f_settings:
            f_settings.writelines([f"{key} = {value} \n" for (key, value) in self._properties.items()])
            f_settings.flush()
