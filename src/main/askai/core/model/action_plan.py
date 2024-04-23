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
from types import SimpleNamespace


@dataclass(frozen=True)
class ActionPlan:
    """Keep track of the router action plan."""

    reasoning: str = None
    category: str = None
    plan: list[SimpleNamespace] = None

    def __str__(self):
        return f"Action Plan: {json.dumps(self.__dict__, default=lambda obj: obj.__dict__)}"
