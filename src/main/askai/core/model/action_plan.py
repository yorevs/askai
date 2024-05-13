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

from dataclasses import dataclass
from types import SimpleNamespace

from askai.core.askai_messages import msg
from askai.core.model.category import Category


@dataclass
class ActionPlan:
    """Keep track of the router action plan."""

    thoughts: SimpleNamespace = None
    category: str = None
    ultimate_goal: str = None
    actions: list[SimpleNamespace] = None

    @staticmethod
    def final(query: str) -> 'ActionPlan':
        """TODO"""
        plan = ActionPlan()
        plan.category = Category.FINAL_ANSWER.value
        plan.ultimate_goal = query
        plan.actions = [SimpleNamespace(task=f"Answer the human: {query}")]
        return plan

    def __str__(self):
        return (
            f"Objective: {self.reasoning}  "
            f"Observations: {self.thoughts.observations}  "
            f"Criticism: {self.thoughts.criticism}  "
        )

    def __len__(self):
        return len(self.actions)

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

    @property
    def goals(self) -> list[str]:
        """TODO"""
        return self.thoughts.sub_goals + [self.ultimate_goal]
