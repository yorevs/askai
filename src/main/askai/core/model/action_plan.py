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

import json
from dataclasses import dataclass
from types import SimpleNamespace

from askai.core.askai_messages import msg


@dataclass
class ActionPlan:
    """Keep track of the router action plan."""

    thoughts: SimpleNamespace = None
    category: str = None
    ultimate_goal: str = None
    actions: list[SimpleNamespace] = None

    def __str__(self):
        return f"Action Plan: {json.dumps(self.__dict__, default=lambda obj: obj.__dict__)}"

    def __len__(self):
        return len(self.actions)

    @property
    def speak(self) -> str:
        """TODO"""
        return msg.translate(self.thoughts.speak)
