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
import logging as log
import os
import random
from collections import defaultdict
from typing import AnyStr, Optional

import pause
from langchain_core.prompts import PromptTemplate
from transitions import Machine

from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.enums.acc_color import AccColor
from askai.core.model.acc_response import AccResponse
from askai.core.model.action_plan import ActionPlan
from askai.core.model.model_result import ModelResult
from askai.core.processors.splitter.splitter_actions import actions
from askai.core.processors.splitter.splitter_states import States
from askai.core.processors.splitter.splitter_transitions import Transition, TRANSITIONS
from askai.core.router.evaluation import assert_accuracy, EVALUATION_GUIDE
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InterruptionRequest, TerminatingQuery


class SplitterPipeline:
    """TODO"""

    state: States

    FAKE_SLEEP: float = 0.3

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
        self._final_answer: Optional[str] = None
        self._model: ModelResult | None = None
        self._resp_history: list[str] = list()

    @property
    def iteractions(self) -> int:
        return self._iteractions

    @iteractions.setter
    def iteractions(self, value: int):
        self._iteractions = value

    @property
    def failures(self) -> dict[str, int]:
        return self._failures

    @property
    def plan(self) -> ActionPlan:
        return self._plan

    @property
    def model(self) -> ModelResult:
        return self._model

    @property
    def previous(self) -> States:
        return self._previous

    @property
    def query(self) -> str:
        return self._query

    @property
    def final_answer(self) -> Optional[str]:
        return self._final_answer

    @property
    def resp_history(self) -> list[str]:
        return self._resp_history

    def track_previous(self) -> None:
        """TODO"""
        self._previous = self.state

    def has_next(self) -> bool:
        """TODO"""
        return len(self.plan.tasks) > 0 if self.plan and self.plan.tasks else False

    def is_direct(self) -> bool:
        """TODO"""
        return self.plan.is_direct if self.plan else True

    def st_startup(self) -> bool:
        log.info("Task Splitter pipeline has started!")
        return True

    def st_model_select(self) -> bool:
        log.info("Selecting response model...")
        self._model = ModelResult.default()
        return True

    def st_task_split(self) -> bool:
        log.info("Splitting tasks...")
        self._plan = actions.split(self.query, self.model)
        if self._plan.is_direct:
            self._final_answer = self._plan.speak or msg.no_output("TaskSplitter")
        return True

    def st_execute_next(self) -> bool:
        _iter_ = self.plan.tasks.copy().__iter__()
        if action := next(_iter_, None):
            if agent_output := actions.process_action(action):
                self.resp_history.append(agent_output)
                self.plan.tasks.pop(0)
        return False

    def st_accuracy_check(self) -> AccColor:

        # FIXME Hardcoded for now
        pass_threshold: AccColor = AccColor.GOOD

        if self.is_direct:
            ai_response: str = self.final_answer
        else:
            ai_response: str = os.linesep.join(self._resp_history)

        acc: AccResponse = assert_accuracy(self.query, ai_response, pass_threshold)

        if acc.is_interrupt:
            # AI flags that it can't continue interacting.
            log.warning(msg.interruption_requested(ai_response))
            raise InterruptionRequest(ai_response)
        elif acc.is_terminate:
            # AI flags that the user wants to end the session.
            raise TerminatingQuery(ai_response)
        elif acc.is_pass(pass_threshold):
            shared.memory.save_context({"input": self.query}, {"output": self.final_answer})
        else:
            acc_template = PromptTemplate(input_variables=["problems"], template=prompt.read_prompt("acc-report"))
            # Include the guidelines for the first mistake.
            if not shared.context.get("EVALUATION"):
                shared.context.push("EVALUATION", EVALUATION_GUIDE)
            shared.context.push("EVALUATION", acc_template.format(problems=acc.details))

        return acc.acc_color

    def st_refine_answer(self) -> bool:
        result = random.choice([True, False])
        pause.seconds(self.FAKE_SLEEP)
        return result

    def st_final_answer(self) -> bool:
        self._final_answer = "This is the final answer"
        result = random.choice([True, False])
        pause.seconds(self.FAKE_SLEEP)
        return result
