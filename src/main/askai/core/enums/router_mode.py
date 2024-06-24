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

from hspylib.core.enums.enumeration import Enumeration


class RouterMode(Enumeration):
    """The available router modes used to provide an answer to the user."""

    # fmt: on

    TASK_SPLIT          = 'TaskSplitter'

    QNA                 = 'QuestionsAndAnswers'

    CUSTOM_PROMPT       = 'Custom Prompts'

    NON_INTERACTIVE     = 'Non-Interactive'

    # fmt: off
