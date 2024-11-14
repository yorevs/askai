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
from askai.core.askai_configs import configs
from askai.core.askai_messages import msg
from askai.core.enums.acc_color import AccColor
from askai.core.enums.response_model import ResponseModel
from askai.core.model.acc_response import AccResponse
from askai.core.model.action_plan import ActionPlan
from askai.core.model.model_result import ModelResult
from askai.core.processors.splitter.splitter_actions import actions
from askai.core.processors.splitter.splitter_result import PipelineResponse, SplitterResult
from askai.core.processors.splitter.splitter_states import States
from askai.core.processors.splitter.splitter_transitions import Transition, TRANSITIONS
from askai.core.router.evaluation import eval_response, EVALUATION_GUIDE
from askai.core.support.shared_instances import shared
from collections import defaultdict
from hspylib.core.preconditions import check_state
from hspylib.core.tools.dict_tools import get_or_default
from hspylib.core.tools.validator import Validator
from langchain_core.prompts import PromptTemplate
from textwrap import dedent
from transitions import Machine
from typing import AnyStr, Optional

import logging as log


class SplitterPipeline:
    """TODO"""

    state: States

    FAKE_SLEEP: float = 0.3

    def __init__(self, query: AnyStr):
        self._transitions: list[Transition] = [t for t in TRANSITIONS]
        self._machine: Machine = Machine(
            name="TaskSplitterMachine",
            model=self,
            initial=States.STARTUP,
            states=States,
            transitions=self._transitions,
            auto_transitions=False,
        )
        self._query: str = query
        self._previous: States = States.NOT_STARTED
        self._result: SplitterResult = SplitterResult(query)
        self._iteractions: int = 0
        self._failures: dict[str, int] = defaultdict(int)

    @property
    def query(self) -> str:
        return self._query

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
    def last_response(self) -> PipelineResponse:
        try:
            return get_or_default(self.responses, -1)
        except IndexError:
            return PipelineResponse(self.query)

    @property
    def last_query(self) -> Optional[str]:
        return self.last_response.query

    @last_query.setter
    def last_query(self, value: str) -> None:
        self.last_response.query = value

    @property
    def last_answer(self) -> Optional[str]:
        return self.last_response.answer

    @last_answer.setter
    def last_answer(self, value: str) -> None:
        self.last_response.answer = value

    @property
    def last_accuracy(self) -> Optional[AccResponse]:
        return self.last_response.accuracy

    @last_accuracy.setter
    def last_accuracy(self, value: AccResponse) -> None:
        self.last_response.accuracy = value

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
        """Track the previous state of pipeline execution."""
        self._previous = self.state

    def has_next(self) -> bool:
        """Check if the plan has more actions to be executed to complete it.
        :return: True if the plan is there are still actions pending, otherwise False.
        """
        return len(self.plan.tasks) > 0 if self.plan is not None and self.plan.tasks else False

    def is_direct(self) -> bool:
        """Check if the plan is direct or if there are actions to be executed to complete it.
        :return: True if the plan is direct, otherwise False.
        """
        return self.plan.is_direct if self.plan is not None else True

    def st_startup(self) -> bool:
        """Pipeline-State::Startup Pipeline startup process.
        :return: Boolean indicating success or failure after processing the state.
        """

        log.info("Task Splitter pipeline has started!")

        return True

    def st_model_select(self) -> bool:
        """Pipeline-State::ModeSelect Select the response model to process the user request.
        :return: Boolean indicating success or failure after processing the state.
        """

        log.info("Selecting response model...")
        # FIXME: Model select is default for now
        self.model = ModelResult.default()

        return True

    def st_task_split(self) -> bool:
        """Pipeline-State::TaskSplit Split the user query into small atomic actionable tasks, and create an
        execution plan to execute them all.
        :return: Boolean indicating success or failure after processing the state.
        """
        log.info("Splitting tasks...")
        if (plan := actions.split(self.question, self.model)) is not None:
            if plan.is_direct:
                self.responses.append(PipelineResponse(self.question, plan.speak or msg.no_output("TaskSplitter")))
            self.plan = plan
            return True

        return False

    def st_execute_task(self) -> bool:
        """Pipeline-State::ExecuteTask Execute the action requested by the AI to complete the user query.
        :return: Boolean indicating success or failure after processing the state.
        """

        check_state(self.plan.tasks is not None and len(self.plan.tasks) > 0)
        _iter_ = self.plan.tasks.copy().__iter__()
        if action := next(_iter_, None):
            log.info(f"Executing task '{action}'...")
            if agent_output := actions.process_action(action):
                self.responses.append(PipelineResponse(action.task, agent_output))
                return True

        return False

    def st_accuracy_check(self, pass_threshold: AccColor = configs.pass_threshold) -> AccColor:
        """Pipeline-State::AccuracyCheck Checks whether the AI response is complete enough to present to the user.
        :param pass_threshold: Threshold value used to determine passing accuracy.
        :return: AccColor indicating success or failure after processing the state.
        """

        if not Validator.has_no_nulls(self.last_query, self.last_answer):
            return AccColor.BAD

        # fmt: off
        issue_report: str = dedent("""\
        The (AI-Assistant) provided an incomplete response.
        Enhance future responses by directly addressing the following details:

        ---
        {problems}
        ---

        If unsure, respond with: 'I don't know.' Do not generate speculative answers.
        """).strip()
        # fmt: off

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
        else:
            if self.responses:
                self.responses.pop(0)
            acc_template = PromptTemplate(input_variables=["problems"], template=issue_report)
            if not shared.context.get("EVALUATION"):  # Include the guidelines for the first mistake.
                shared.context.push("EVALUATION", EVALUATION_GUIDE)
            shared.context.push("EVALUATION", acc_template.format(problems=acc.details))

        self.last_accuracy = acc

        return acc.acc_color

    def st_refine_answer(self) -> bool:
        """Pipeline-State::RefineAnswer Refines the answer to present to the user.
        :return: Boolean indicating success or failure after processing the state.
        """

        if refined := actions.refine_answer(self.question, self.final_answer, self.last_accuracy):
            final_response: PipelineResponse = PipelineResponse(self.question, refined, self.last_accuracy)
            self.responses.clear()
            self.responses.append(final_response)
            return True

        return False

    def st_final_answer(self) -> bool:
        """Pipeline-State::FinalAnswer Wraps the final answer to present to the user.
        :return: Boolean indicating success or failure after processing the state.
        """

        model: ModelResult = (
            ModelResult(ResponseModel.ASSISTIVE_TECH_HELPER.model, self.model.goal, self.model.reason)
            if configs.is_assistive
            else self.model
        )

        if wrapped := actions.wrap_answer(self.question, self.final_answer, model):
            final_response: PipelineResponse = PipelineResponse(self.question, wrapped, self.last_accuracy)
            self.responses.clear()
            self.responses.append(final_response)
            return True

        return False
