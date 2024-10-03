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
from hspylib.modules.application.exit_status import ExitStatus

from askai.core.model.api_keys import ApiKeys
from clitt.core.term.commons import is_a_tty
from hspylib.core.metaclass.classpath import Classpath
from hspylib.core.tools.commons import is_debugging, parent_path, root_dir

import logging as log
import os
import pydantic
import sys
import warnings

if not is_debugging():
    warnings.simplefilter("ignore", category=FutureWarning)
    warnings.simplefilter("ignore", category=UserWarning)
    warnings.simplefilter("ignore", category=DeprecationWarning)
    warnings.simplefilter("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", module="chromadb.db.impl.sqlite")

if not is_a_tty():
    log.getLogger().setLevel(log.ERROR)

if not os.environ.get("USER_AGENT"):
    # The AskAI User Agent, required by the langchain framework
    ASKAI_USER_AGENT: str = "AskAI-User-Agent"
    os.environ["USER_AGENT"] = ASKAI_USER_AGENT

# If running from GitHub actions, we can't set those
if not os.environ.get("GITHUB_ACTIONS"):
    try:
        API_KEYS: ApiKeys = ApiKeys()
    except pydantic.v1.error_wrappers.ValidationError as err:
        if not ApiKeys.prompt():
            log.error(err.json())
            sys.exit(ExitStatus.ABNORMAL)


class _Classpath(Classpath):
    """A class for managing classpath-related operations. Uses the Classpath metaclass."""

    def __init__(self):
        super().__init__(parent_path(__file__), parent_path(root_dir()), (parent_path(__file__) / "resources"))


# Instantiate the classpath singleton
assert (classpath := _Classpath().INSTANCE) is not None, "Failed to create Classpath instance"
