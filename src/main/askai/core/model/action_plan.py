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

from dataclasses import dataclass, field
from types import SimpleNamespace

from askai.core.askai_messages import msg
from askai.core.model.model_result import ModelResult


@dataclass
class ActionPlan:
    """Keep track of the router action plan."""

    question: str = None
    primary_goal: str = None
    sub_goals: list[str] = None
    thoughts: SimpleNamespace = None
    tasks: list[SimpleNamespace] = None
    model: ModelResult = field(default_factory=ModelResult.default)

    def __str__(self):
        sub_goals: str = "  ".join(f"{i + 1}. {g}" for i, g in enumerate(self.sub_goals))
        tasks: str = ".  ".join([f"{i + 1}. {a.task}" for i, a in enumerate(self.tasks)])
        return (
            f"`Question:` {self.question}  "
            f"`Reasoning:` {self.reasoning}  "
            f"`Observations:` {self.thoughts.observations}  "
            f"`Criticism:` {self.thoughts.criticism}  "
            f"`Speak:` {self.thoughts.speak}  "
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
