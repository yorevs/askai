#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.model.action_plan
      @file: action_plan.py
   @created: Fri, 19 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.model.model_result import ModelResult
from askai.core.support.llm_parser import parse_field, parse_list, parse_word
from dataclasses import dataclass, field
from hspylib.core.preconditions import check_state
from types import SimpleNamespace

import re


@dataclass
class ActionPlan:
    """Represents and tracks the action plan for a router.
    This class is used to keep track of the sequence of actions or steps to be executed by the router.
    """

    question: str = None
    speak: str = None
    primary_goal: str = None
    sub_goals: list[SimpleNamespace] = field(default_factory=list)
    tasks: list[SimpleNamespace] = field(default_factory=list)
    model: ModelResult = field(default_factory=ModelResult.default)

    @staticmethod
    def create(question: str, message: str, model: ModelResult) -> "ActionPlan":
        """Create an ActionPlan based on the provided question, AI message, and result model.
        :param question: The original question or command that was sent to the AI.
        :param message: The AIMessage object containing the AI's response and metadata.
        :param model: The result model.
        :return: An instance of ActionPlan created from the provided inputs.
        """
        plan: ActionPlan = ActionPlan._parse_response(question, message)
        check_state(
            plan is not None and isinstance(plan, ActionPlan), f"Invalid action plan received from LLM: {type(plan)}"
        )
        plan.model = model

        return plan

    @staticmethod
    def _parse_response(question: str, response: str) -> "ActionPlan":
        """Parse the router's response and convert it into an ActionPlan.
        :param question: The original question or command that was sent to the router.
        :param response: The router's response.
        :return: An instance of ActionPlan created from the parsed response.
        """

        speak: str = parse_field("@speak", response)
        primary_goal: str = parse_field("@primary_goal", response)
        sub_goals: list[SimpleNamespace] = parse_list("@sub_goals", response)
        tasks: list[SimpleNamespace] = parse_list("@tasks", response)
        direct: str = parse_word("direct", response)

        # fmt: off
        if primary_goal and tasks:
            plan = ActionPlan(
                question=question,
                speak=speak,
                primary_goal=primary_goal,
                sub_goals=sub_goals,
                tasks=tasks
            )
        elif direct and len(direct) > 1:
            plan = ActionPlan._direct_answer(question, response, ModelResult.default())
        else:
            plan = ActionPlan._direct_task(question, response, ModelResult.default())
        # fmt: on

        return plan

    @staticmethod
    def _direct_answer(question: str, response: str, model: ModelResult) -> "ActionPlan":
        """Create a simple ActionPlan from an AI's direct response in plain text.
        :param question: The original question that was sent to the AI.
        :param response: The AI's direct response in plain text (unformatted JSON).
        :param model: The result model.
        :return: An instance of ActionPlan created from the direct response.
        """
        flags: int = re.IGNORECASE | re.MULTILINE | re.DOTALL
        speak: str = re.sub(r"\*\*Direct:\*\*(.+?)", "\1", response, flags)

        return ActionPlan(question, speak, "N/A", [], [], model)

    @staticmethod
    def _direct_task(question: str, response: str, model: ModelResult) -> "ActionPlan":
        """Create a simple ActionPlan from an AI's direct response in plain text.
        :param question: The original question that was sent to the AI.
        :param response: The AI's direct response in plain text (unformatted JSON).
        :param model: The result model.
        :return: An instance of ActionPlan created from the direct response.
        """
        tasks: list[SimpleNamespace] = [SimpleNamespace(id="1", task=response)]

        return ActionPlan(question, "", "N/A", [], tasks, model)

    def __str__(self):
        sub_goals: str = "  ".join(f"{i + 1}. {g}" for i, g in enumerate(self.sub_goals)) if self.sub_goals else "N/A"
        tasks: str = ".  ".join([f"{i + 1}. {a.task}" for i, a in enumerate(self.tasks)]) if self.tasks else "N/A"
        return (
            f"`Question:` {self.question}  "
            f"`Speak:` {self.speak}  "
            f"`Primary-Goal:` {self.primary_goal}  "
            f"`Sub-Goals:` [{sub_goals}]  "
            f"`Tasks:` [{tasks}]  "
        )

    def __len__(self):
        return len(self.tasks)

    def __eq__(self, other: "ActionPlan") -> bool:
        """TODO"""
        return (
            self.question == other.question
            and self.speak == other.speak
            and self.primary_goal == other.primary_goal
            and self.sub_goals == other.sub_goals
            and self.tasks == other.tasks
        )
