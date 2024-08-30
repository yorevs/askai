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
    """Represents and tracks the action plan for a router.
    This class is used to keep track of the sequence of actions or steps to be executed by the router.
    """

    question: str = None
    primary_goal: str = None
    sub_goals: list[str] = None
    thoughts: SimpleNamespace = None
    tasks: list[SimpleNamespace] = None
    model: ModelResult = field(default_factory=ModelResult.default)

    @staticmethod
    def _parse_response(question: str, response: str) -> "ActionPlan":
        """Parse the router's response and convert it into an ActionPlan.
        :param question: The original question or command that was sent to the router.
        :param response: The router's response, typically a JSON blob. Note that the response might sometimes be a
                         plain JSON string.
        :return: An instance of ActionPlan created from the parsed response.
        """
        json_string = response
        if re.match(r"^`{3}(.+)`{3}$", response):
            _, json_string = extract_codeblock(response)
        plan: ActionPlan = object_mapper.of_json(json_string, ActionPlan)
        if not isinstance(plan, ActionPlan):
            plan = ActionPlan._direct(question, json_string, ModelResult.default())
        return plan

    @staticmethod
    def _direct(question: str, response: str, model: ModelResult) -> "ActionPlan":
        """Create a simple ActionPlan from an AI's direct response in plain text.
        :param question: The original question that was sent to the AI.
        :param response: The AI's direct response in plain text (unformatted JSON).
        :param model: The result model.
        :return: An instance of ActionPlan created from the direct response.
        """
        return ActionPlan(
            question,
            "N/A",
            [],
            SimpleNamespace(reasoning="N/A", observations="N/A", criticism="N/A", speak=response),
            [SimpleNamespace(id="1", task=response)],
            model,
        )

    @staticmethod
    def create(question: str, message: AIMessage, model: ModelResult) -> "ActionPlan":
        """Create an ActionPlan based on the provided question, AI message, and result model.
        :param question: The original question or command that was sent to the AI.
        :param message: The AIMessage object containing the AI's response and metadata.
        :param model: The result model.
        :return: An instance of ActionPlan created from the provided inputs.
        """
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
