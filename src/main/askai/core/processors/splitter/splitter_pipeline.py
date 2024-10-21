#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processors.splitter.splitter_pipeline
      @file: ai_engine.py
   @created: Mon, 21 Oct 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import random
from collections import defaultdict
from typing import AnyStr

import pause
from transitions import Machine

from askai.core.enums.acc_color import AccColor
from askai.core.model.action_plan import ActionPlan
from askai.core.processors.splitter.splitter_states import States
from askai.core.processors.splitter.splitter_transitions import Transition, TRANSITIONS


class SplitterPipeline:
    """TODO"""

    state: States

    FAKE_SLEEP: int = 1

    def __init__(self, query: AnyStr):
        self._transitions: list[Transition] = [t for t in TRANSITIONS]
        self._machine: Machine = Machine(
            name="Taius-Coder",
            model=self,
            initial=States.STARTUP,
            states=States,
            transitions=self._transitions,
            auto_transitions=False
        )
        self._previous: States | None = None
        self._failures: dict[str, int] = defaultdict(int)
        self._iteractions: int = 0
        self._query: str = query
        self._plan: ActionPlan | None = None

    @property
    def failures(self) -> dict[str, int]:
        return self._failures

    @property
    def plan(self) -> ActionPlan:
        return self._plan

    @property
    def previous(self) -> States:
        return self._previous

    def track_previous(self) -> None:
        self._previous = self.state

    def has_next(self) -> bool:
        """TODO"""
        return len(self.plan.tasks) > 0 if self.plan else False

    def is_direct(self) -> bool:
        """TODO"""
        return self.plan.is_direct if self.plan else True

    def st_startup(self) -> bool:
        result = random.choice([True, False])
        pause.seconds(self.FAKE_SLEEP)
        return result

    def st_query_queued(self) -> bool:
        result = random.choice([True, False])
        pause.seconds(self.FAKE_SLEEP)
        return result

    def st_model_select(self) -> bool:
        result = random.choice([True, False])
        pause.seconds(self.FAKE_SLEEP)
        return result

    def st_task_split(self) -> tuple[bool, bool]:
        result1, result2 = random.choice([True, False]), random.choice([True, False])
        pause.seconds(self.FAKE_SLEEP)
        return result1, result2

    def st_execute_next(self) -> tuple[AccColor, bool]:
        color = AccColor.value_of(random.choice(AccColor.names()))
        result = random.choice([True, False])
        pause.seconds(self.FAKE_SLEEP)
        return color, result

    def st_accuracy_check(self) -> AccColor:
        color = AccColor.value_of(random.choice(AccColor.names()))
        pause.seconds(self.FAKE_SLEEP)
        return color

    def st_refine_answer(self) -> bool:
        result = random.choice([True, False])
        pause.seconds(self.FAKE_SLEEP)
        return result
