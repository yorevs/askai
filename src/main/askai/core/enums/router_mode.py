#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: router_mode.py
   @created: Tue, 24 Jun 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from typing import Optional

from hspylib.core.enums.enumeration import Enumeration

from askai.core.askai_configs import configs
from askai.core.features.router.ai_processor import AIProcessor
from askai.core.features.router.procs.free_form import free_form
from askai.core.features.router.procs.qna import qna
from askai.core.features.router.procs.task_splitter import splitter


class RouterMode(Enumeration):
    """The available router modes used to provide an answer to the user."""

    # fmt: on

    TASK_SPLIT          = 'Task Splitter', splitter

    QNA                 = 'Questions and Answers', qna

    NON_INTERACTIVE     = 'Non-Interactive', free_form

    DEFAULT             = 'Task Splitter', splitter if configs.is_interactive else 'Non-Interactive', free_form

    # fmt: off

    def __str__(self):
        return self.value[0]

    @property
    def mode(self) -> str:
        return self.value[0]

    @property
    def processor(self) -> AIProcessor:
        return self.value[1]

    @property
    def is_default(self) -> bool:
        return self == RouterMode.DEFAULT

    def process(self, question: str, **kwargs) -> Optional[str]:
        """TODO"""
        return self.processor.process(question, **kwargs)
