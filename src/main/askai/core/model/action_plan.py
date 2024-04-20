#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.model.action_plan
      @file: action_plan.py
   @created: Fri, 19 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""

import json
from dataclasses import dataclass
from functools import cached_property
from types import SimpleNamespace
from typing import Any


@dataclass(frozen=True)
class ActionPlan:
    """Keep track of the router action plan."""

    @dataclass
    class Action:
        """Represents a single action."""

        tool: str
        params: list[Any]

    reasoning: str = None
    category: str = None
    plan: list[SimpleNamespace] = None

    @cached_property
    def actions(self) -> list[Action]:
        return [self.Action(a.action, a.inputs) for a in self.plan]

    def __str__(self):
        return f"Action Plan: {json.dumps(self.__dict__, default=lambda obj: obj.__dict__)}"
