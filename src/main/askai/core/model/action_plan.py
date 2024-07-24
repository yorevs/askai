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
from askai.core.support.utilities import extract_codeblock
from dataclasses import dataclass, field
from hspylib.core.object_mapper import object_mapper
from hspylib.core.preconditions import check_state
from langchain_core.messages import AIMessage
from types import SimpleNamespace
from typing import Optional

import re


@dataclass
class ActionPlan:
    """Keep track of the router action plan."""

    question: str = None
    primary_goal: str = None
    sub_goals: list[str] = None
    thoughts: SimpleNamespace = None
    tasks: list[SimpleNamespace] = None
    model: ModelResult = field(default_factory=ModelResult.default)

    @staticmethod
    def _parse_response(question: str, response: str) -> "ActionPlan":
        """Parse the router response.
        :param response: The router response. This should be a JSON blob, but sometimes the AI responds with a
        straight JSON string.
        """
        json_string = response
        if re.match(r"^`{3}(.+)`{3}$", response):
            _, json_string = extract_codeblock(response)
        plan: ActionPlan = object_mapper.of_json(json_string, ActionPlan)
        if not isinstance(plan, ActionPlan):
            plan = ActionPlan._final(question, json_string, ModelResult.default())

        return plan

    @staticmethod
    def _final(question: str, response: str, model: ModelResult) -> "ActionPlan":
        """TODO"""
        return ActionPlan(
            question,
            f"Answer to the question: {question}",
            [],
            SimpleNamespace(
                reasoning="AI decided to respond directly",
                observations="AI had enough context to respond directly",
                criticism="The answer may not be good enough",
                speak=response,
            ),
            [SimpleNamespace(id="1", task=response)],
            model,
        )

    @staticmethod
    def _browse(question: str, query: str, model: ModelResult) -> "ActionPlan":
        """TODO"""
        return ActionPlan(
            question,
            f"Answer to the question: {question}",
            [],
            SimpleNamespace(
                reasoning="AI requested internet browsing",
                observations="",
                criticism="The answer may not be too accurate",
                speak="I will search on the internet for you",
            ),
            [SimpleNamespace(id="1", task=f"Browse on te internet for: {query}")],
            model,
        )

    @staticmethod
    def _terminal(question: str, cmd_line: str, model: ModelResult) -> "ActionPlan":
        """TODO"""
        return ActionPlan(
            question,
            f"Execute terminal command: {question}",
            [],
            SimpleNamespace(
                reasoning="AI requested to execute a terminal command",
                observations="",
                criticism="The user needs to grant access",
                speak="",
            ),
            [SimpleNamespace(id="1", task=f"Execute the following command on the terminal: {cmd_line}")],
            model,
        )

    @staticmethod
    def create(question: str, message: AIMessage, model: ModelResult) -> "ActionPlan":
        """TODO"""
        plan: ActionPlan = ActionPlan._parse_response(question, message.content)
        check_state(
            plan is not None and isinstance(plan, ActionPlan), f"Invalid action plan received from LLM: {type(plan)}"
        )
        plan.model = model

        return plan

    def __str__(self):
        sub_goals: str = "  ".join(f"{i + 1}. {g}" for i, g in enumerate(self.sub_goals)) if self.sub_goals else "N/A"
        tasks: str = ".  ".join([f"{i + 1}. {a.task}" for i, a in enumerate(self.tasks)]) if self.tasks else "N/A"
        return (
            f"`Question:` {self.question}  "
            f"`Reasoning:` {self.reasoning}  "
            f"`Observations:` {self.observations}  "
            f"`Criticism:` {self.criticism}  "
            f"`Speak:` {self.speak}  "
            f"`Sub-Goals:` [{sub_goals}]  "
            f"`Tasks:` [{tasks}]  ."
        )

    def __len__(self):
        return len(self.tasks)

    @property
    def reasoning(self) -> Optional[str]:
        return self.thoughts.reasoning if hasattr(self, "thoughts") and hasattr(self.thoughts, "reasoning") else None

    @property
    def observations(self) -> Optional[str]:
        return (
            self.thoughts.observations if hasattr(self, "thoughts") and hasattr(self.thoughts, "observations") else None
        )

    @property
    def criticism(self) -> Optional[str]:
        return self.thoughts.criticism if hasattr(self, "thoughts") and hasattr(self.thoughts, "criticism") else None

    @property
    def speak(self) -> Optional[str]:
        return self.thoughts.speak if hasattr(self, "thoughts") and hasattr(self.thoughts, "speak") else None
