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

from askai.core.askai_messages import msg
from askai.core.model.category import Category
from dataclasses import dataclass
from types import SimpleNamespace

from askai.core.model.model_result import ModelResult


@dataclass
class ActionPlan:
    """Keep track of the router action plan."""

    thoughts: SimpleNamespace = None
    model: ModelResult = None
    sub_goals: list[str] = None
    tasks: list[SimpleNamespace] = None

    @staticmethod
    def final(query: str) -> "ActionPlan":
        """TODO"""
        plan = ActionPlan()
        plan.category = Category.FINAL_ANSWER.value
        plan.primary_goal = query
        plan.tasks = [SimpleNamespace(task=f"Answer the human: {query}")]
        return plan

    def __str__(self):
        sub_goals: str = "  ".join(f"{i + 1}. {g}" for i, g in enumerate(self.sub_goals))
        tasks: str = ".  ".join([f"{i + 1}. {a.task}" for i, a in enumerate(self.tasks)])
        return (
            f"Reasoning: {self.reasoning}  "
            f"Observations: {self.thoughts.observations}  "
            f"Criticism: {self.thoughts.criticism}  "
            f"Sub-Goals: [{sub_goals}]  "
            f"Tasks: [{tasks}]  ."
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
