#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.router.router
      @file: task_splitter.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.processors.splitter.splitter_executor import SplitterExecutor
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse, TerminatingQuery
from hspylib.core.exception.exceptions import InvalidArgumentError
from hspylib.core.metaclass.singleton import Singleton
from pathlib import Path
from pydantic_core import ValidationError
from typing import Any, Optional, Type, TypeAlias

import logging as log
import os

AgentResponse: TypeAlias = dict[str, Any]


class TaskSplitter(metaclass=Singleton):
    """Processor to provide a divide and conquer set of tasks to fulfill an objective. This is responsible for the
    orchestration and execution of the smaller tasks."""

    INSTANCE: "TaskSplitter"

    # fmt: off
    # Allow the router to retry on the errors bellow.
    RETRIABLE_ERRORS: tuple[Type[Exception], ...] = (
        InaccurateResponse,
        InvalidArgumentError,
        ValidationError
    )
    # fmt: on

    def process(self, question: str, **_) -> Optional[str]:
        """Process the user question by splitting complex tasks into smaller single actionable tasks.
        :param question: The user question to process.
        """

        if not question or question.casefold() in ["exit", "leave", "quit", "q"]:
            raise TerminatingQuery("The user wants to exit!")

        executor = SplitterExecutor(question)
        os.chdir(Path.home())
        shared.context.forget("EVALUATION")  # Erase previous evaluation notes.
        log.info("TaskSplitter::[QUESTION] '%s'", question)
        executor.start()
        executor.join()  # Wait for the pipeline execution.

        return executor.pipeline.final_answer


assert (splitter := TaskSplitter().INSTANCE) is not None
