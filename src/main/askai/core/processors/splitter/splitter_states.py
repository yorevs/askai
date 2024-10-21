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
from hspylib.core.enums.enumeration import Enumeration


class States(Enumeration):
    """Enumeration of possible task splitter states."""
    # fmt: off
    STARTUP         = 'Processing query'
    MODEL_SELECT    = 'Selecting Model'
    TASK_SPLIT      = 'Splitting Task'
    ACCURACY_CHECK  = 'Checking Accuracy'
    EXECUTE_TASK    = 'Executing Task'
    REFINE_ANSWER   = 'Refining Answer'
    COMPLETE        = 'Completed'
    # fmt: on
