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
from collections import defaultdict
from typing import AnyStr

from hspylib.core.preconditions import check_state
from langchain_core.prompts import PromptTemplate
from transitions import Machine

from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.enums.acc_color import AccColor
from askai.core.model.acc_response import AccResponse
from askai.core.model.action_plan import ActionPlan
from askai.core.model.model_result import ModelResult
from askai.core.processors.splitter.splitter_actions import actions
from askai.core.processors.splitter.splitter_result import SplitterResult, PipelineResponse
from askai.core.processors.splitter.splitter_states import States
from askai.core.processors.splitter.splitter_transitions import Transition, TRANSITIONS
from askai.core.router.evaluation import eval_response, EVALUATION_GUIDE
from askai.core.support.shared_instances import shared


class SplitterPipeline:
    """TODO"""

    state: States

    FAKE_SLEEP: float = 0.3

    def __init__(self, question: AnyStr):
        self._transitions: list[Transition] = [t for t in TRANSITIONS]
        self._machine: Machine = Machine(
            name="Taius-Coder", model=self,
            initial=States.STARTUP, states=States, transitions=self._transitions,
            auto_transitions=False
        )
        self._previous: States = States.NOT_STARTED
        self._iteractions: int = 0
        self._failures: dict[str, int] = defaultdict(int)
        self._result: SplitterResult = SplitterResult(question)

    @property
    def previous(self) -> States:
        return self._previous

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
    def result(self) -> SplitterResult:
        return self._result

    @property
    def responses(self) -> list[PipelineResponse]:
        return self._result.responses

    @property
    def question(self) -> str:
        return self.result.question

    @property
    def last_query(self) -> str:
        return self.responses[-1].query

    @last_query.setter
    def last_query(self, value: str) -> None:
        self.responses[-1].query = value

    @property
    def last_answer(self) -> str:
        return self.responses[-1].answer

    @last_answer.setter
    def last_answer(self, value: str) -> None:
        self.responses[-1].answer = value

    @property
    def last_accuracy(self) -> AccResponse:
        return self.responses[-1].accuracy

    @last_accuracy.setter
    def last_accuracy(self, value: AccResponse) -> None:
        self.responses[-1].accuracy = value

    @property
    def plan(self) -> ActionPlan:
        return self.result.plan

    @plan.setter
    def plan(self, value: ActionPlan):
        self.result.plan = value

    @property
    def model(self) -> ModelResult:
        return self.result.model

    @model.setter
    def model(self, value: ModelResult):
        self.result.model = value

    @property
    def final_answer(self) -> str:
        return self.result.final_response()

    def track_previous(self) -> None:
        """TODO"""
        self._previous = self.state

    def has_next(self) -> bool:
        """TODO"""
        return len(self.plan.tasks) > 0 if self.plan is not None and self.plan.tasks else False

    def is_direct(self) -> bool:
        """TODO"""
        return self.plan.is_direct if self.plan is not None else True

    def st_startup(self) -> bool:
        """TODO"""
        log.info("Task Splitter pipeline has started!")
        return True

    def st_model_select(self) -> bool:
        """TODO"""
        log.info("Selecting response model...")
        # FIXME: Model select is default for now
        self.model = ModelResult.default()
        return True

    def st_task_split(self) -> bool:
        """TODO"""
        log.info("Splitting tasks...")
        if (plan := actions.split(self.question, self.model)) is not None:
            if plan.is_direct:
                self.responses.append(PipelineResponse(self.question, plan.speak or msg.no_output("TaskSplitter")))
            self.plan = plan
            return True
        return False

    def st_execute_task(self) -> bool:
        """TODO"""
        check_state(self.plan.tasks is not None and len(self.plan.tasks) > 0)
        _iter_ = self.plan.tasks.copy().__iter__()
        if action := next(_iter_, None):
            log.info(f"Executing task '{action}'...")
            if agent_output := actions.process_action(action):
                self.responses.append(PipelineResponse(action.task, agent_output))
                return True
        return False

    def st_accuracy_check(self) -> AccColor:
        """TODO"""

        if self.last_query is None or self.last_answer is None:
            return AccColor.BAD

        # FIXME Hardcoded for now
        pass_threshold: AccColor = AccColor.MODERATE
        acc: AccResponse = eval_response(self.last_query, self.last_answer)

        if acc.is_interrupt:  # AI flags that it can't continue interacting.
            log.warning(msg.interruption_requested(self.last_answer))
            self.plan.tasks.clear()
        elif acc.is_terminate:  # AI flags that the user wants to end the session.
            log.warning(msg.terminate_requested(self.last_answer))
            self.plan.tasks.clear()
        elif acc.is_pass(pass_threshold):  # AI provided a good answer.
            log.info(f"AI provided a good answer: {self.last_answer}")
            if len(self.plan.tasks) > 0:
                self.plan.tasks.pop(0)
            shared.memory.save_context({"input": self.last_query}, {"output": self.last_answer})
        else:
            if len(self.responses) > 0:
                self.responses.pop(0)
            acc_template = PromptTemplate(input_variables=["problems"], template=prompt.read_prompt("acc-report"))
            if not shared.context.get("EVALUATION"):  # Include the guidelines for the first mistake.
                shared.context.push("EVALUATION", EVALUATION_GUIDE)
            shared.context.push("EVALUATION", acc_template.format(problems=acc.details))

        self.last_accuracy = acc

        return acc.acc_color

    def st_refine_answer(self) -> bool:
        return actions.refine_answer(self.question, self.final_answer, self.last_accuracy)

    def st_final_answer(self) -> bool:
        return actions.wrap_answer(self.question, self.final_answer, self.model)
