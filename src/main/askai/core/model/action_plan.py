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
import ast
import re
from dataclasses import dataclass, field
from types import SimpleNamespace

from askai.core.model.model_result import ModelResult
from hspylib.core.preconditions import check_state
from langchain_core.messages import AIMessage


@dataclass
class ActionPlan:
    """Represents and tracks the action plan for a router.
    This class is used to keep track of the sequence of actions or steps to be executed by the router.
    """

    question: str = None
    speak: str = None
    primary_goal: str = None
    sub_goals: list[str] = field(default_factory=list)
    tasks: list[SimpleNamespace] = field(default_factory=list)
    model: ModelResult = field(default_factory=ModelResult.default)

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

    @staticmethod
    def _parse_response(question: str, response: str) -> "ActionPlan":
        """Parse the router's response and convert it into an ActionPlan.
        :param question: The original question or command that was sent to the router.
        :param response: The router's response.
        :return: An instance of ActionPlan created from the parsed response.
        """
        flags: int = re.IGNORECASE | re.MULTILINE | re.DOTALL

        # Define patterns for the required fields
        speak_pattern = r"@speak:\s*\"(.+?)\""
        primary_goal_pattern = r"@primary_goal:\s*(.+)"
        sub_goals_pattern = r"@sub_goals:\s*\[(.+?)\]"
        tasks_pattern = r"@tasks:\s*\[(.+?)\]"
        direct_pattern = r"\**Direct:\**\s*(.+?)"

        # Extract using regex
        speak_match = re.search(speak_pattern, response, flags)
        primary_goal_match = re.search(primary_goal_pattern, response, flags)
        sub_goals_match = re.search(sub_goals_pattern, response, flags)
        tasks_match = re.search(tasks_pattern, response, flags)
        direct_match = re.search(direct_pattern, response, flags)

        # Parse fields
        speak = speak_match.group(1) if speak_match else None
        primary_goal = primary_goal_match.group(1) if primary_goal_match else None
        sub_goals = ast.literal_eval(f"[{sub_goals_match.group(1)}]") if sub_goals_match else []
        tasks = ast.literal_eval(f"[{tasks_match.group(1)}]") if tasks_match else []
        tasks = list(map(lambda t: SimpleNamespace(**t), tasks))
        direct = direct_match.group(1) if direct_match else None

        # fmt: off
        if direct:
            plan = ActionPlan._direct_answer(question, response, ModelResult.default())
        elif speak and primary_goal and tasks:
            plan = ActionPlan(
                question=question,
                speak=speak,
                primary_goal=primary_goal,
                sub_goals=sub_goals,
                tasks=tasks
            )
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
