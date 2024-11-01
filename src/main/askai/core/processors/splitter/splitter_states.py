#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processors.splitter.splitter_states
      @file: splitter_states.py
   @created: Mon, 21 Oct 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_messages import msg
from hspylib.core.enums.enumeration import Enumeration


class States(Enumeration):
    """Enumeration of possible task splitter states."""

    # fmt: off
    NOT_STARTED     = 'N/S'

    STARTUP         = 'Thinking'

    MODEL_SELECT    = 'Selecting model'

    TASK_SPLIT      = 'Creating execution plan'

    ACC_CHECK       = 'Checking accuracy'

    EXECUTE_TASK    = 'Executing actions'

    REFINE_ANSWER   = 'Refining answer'

    WRAP_ANSWER     = 'Wrapping answer'

    COMPLETE        = 'Completed'
    # fmt: on

    def __str__(self) -> str:
        return msg.t(self.value)
