#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.model.action_plan
      @file: action_plan.py
   @created: Fri, 19 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import re
from dataclasses import dataclass, field
from types import SimpleNamespace

from hspylib.core.preconditions import check_state
from langchain_core.messages import AIMessage

from askai.core.askai_messages import msg
from askai.core.model.model_result import ModelResult
from askai.core.support.object_mapper import object_mapper
from askai.core.support.utilities import extract_codeblock


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
    def _parse_response(question: str, response: str) -> 'ActionPlan':
        """Parse the router response.
        :param response: The router response. This should be a JSON blob, but sometimes the AI responds with a
        straight JSON string.
        """
        json_string = response
        if re.match(r"^`{3}(.+)`{3}$", response):
            _, json_string = extract_codeblock(response)
        plan: ActionPlan = object_mapper.of_json(json_string, ActionPlan)
        if not isinstance(plan, ActionPlan):
            plan = ActionPlan._direct(question, json_string, ModelResult.default())

        return plan

    @staticmethod
    def _direct(question: str, response: str, model: ModelResult) -> 'ActionPlan':
        """TODO"""
        return ActionPlan(
            question,
            f"Answer the question: {question}", [],
            SimpleNamespace(
                reasoning="AI decided to respond directly", observations="", criticism="", speak=""),
            [SimpleNamespace(id="1", task=response)],
            model
        )

    @staticmethod
    def create(question: str, response: AIMessage, model: ModelResult) -> 'ActionPlan':
        """TODO"""
        if response.content.startswith("DIRECT:"):
            plan: ActionPlan = ActionPlan._direct(question, response.content, model)
        else:
            plan: ActionPlan = ActionPlan._parse_response(question, response.content)
            check_state(
                plan is not None and isinstance(plan, ActionPlan),
                f"Invalid action plan received from LLM: {type(plan)}")
            plan.model = model
            if not plan.tasks:
                plan.tasks.append(SimpleNamespace(id="1", task=f"DIRECT: QUESTION='{question}' ANSWER='{plan.speak}'"))
        return plan

    def __str__(self):
        sub_goals: str = "  ".join(f"{i + 1}. {g}" for i, g in enumerate(self.sub_goals)) if self.sub_goals else "N/A"
        tasks: str = ".  ".join([f"{i + 1}. {a.task}" for i, a in enumerate(self.tasks)]) if self.tasks else "N/A"
        return (
            f"`Question:` {self.question}  "
            f"`Reasoning:` {self.reasoning}  "
            f"`Observations:` {self.thoughts.observations if self.thoughts else 'N/A'}  "
            f"`Criticism:` {self.thoughts.criticism if self.thoughts else 'N/A'}  "
            f"`Speak:` {self.thoughts.speak if self.thoughts else 'N/A'}  "
            f"`Sub-Goals:` [{sub_goals}]  "
            f"`Tasks:` [{tasks}]  ."
        )

    def __len__(self):
        return len(self.tasks)

    @property
    def speak(self) -> str:
        """TODO"""
        return msg.translate(self.thoughts.speak)

    @property
    def reasoning(self) -> str:
        """TODO"""
        return self.thoughts.reasoning

    @property
    def observations(self) -> str:
        """TODO"""
        return self.thoughts.observations

    @property
    def criticism(self) -> str:
        """TODO"""
        return self.thoughts.criticism
