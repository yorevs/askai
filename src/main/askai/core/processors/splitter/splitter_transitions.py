#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processors.splitter.splitter_transitions
      @file: splitter_transitions.py
   @created: Mon, 21 Oct 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from typing import TypeAlias

from askai.core.processors.splitter.splitter_states import States

# Define the transitions between states
Transition: TypeAlias = dict[str, str | States]

# Define transitions from the workflow
TRANSITIONS = [
    {'trigger': 'ev_pipeline_started', 'source': States.STARTUP, 'dest': States.MODEL_SELECT},
    {'trigger': 'ev_model_selected', 'source': States.MODEL_SELECT, 'dest': States.TASK_SPLIT},

    {'trigger': 'ev_direct_answer', 'source': States.TASK_SPLIT, 'dest': States.ACCURACY_CHECK},
    {'trigger': 'ev_plan_created', 'source': States.TASK_SPLIT, 'dest': States.EXECUTE_TASK},

    {'trigger': 'ev_accuracy_check', 'source': States.ACCURACY_CHECK, 'dest': States.EXECUTE_TASK},

    {'trigger': 'ev_task_executed', 'source': States.EXECUTE_TASK, 'dest': States.ACCURACY_CHECK},

    {'trigger': 'ev_accuracy_passed', 'source': States.ACCURACY_CHECK, 'dest': States.EXECUTE_TASK, 'conditions': ['has_next']},
    {'trigger': 'ev_accuracy_passed', 'source': States.ACCURACY_CHECK, 'dest': States.COMPLETE, 'unless': ['has_next']},
    {'trigger': 'ev_accuracy_failed', 'source': States.ACCURACY_CHECK, 'dest': States.EXECUTE_TASK, 'conditions': ['has_next']},
    {'trigger': 'ev_refine_required', 'source': States.ACCURACY_CHECK, 'dest': States.REFINE_ANSWER, 'unless': ['has_next']},

    {'trigger': 'ev_answer_refined', 'source': States.REFINE_ANSWER, 'dest': States.COMPLETE},

    {'trigger': 'ev_task_complete', 'source': States.TASK_SPLIT, 'dest': States.COMPLETE},
]
