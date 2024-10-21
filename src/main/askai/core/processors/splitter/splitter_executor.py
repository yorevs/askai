#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processors.splitter.splitter_executor
      @file: splitter_executor.py
   @created: Mon, 21 Oct 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from threading import Thread

from hspylib.core.decorator.decorators import profiled
from rich.console import Console

from askai.core.askai_configs import configs
from askai.core.enums.acc_color import AccColor
from askai.core.processors.splitter.splitter_pipeline import SplitterPipeline
from askai.core.processors.splitter.splitter_states import States


class SplitterExecutor(Thread):
    """Responsible for executing a Taius Coder pipeline."""

    def __init__(self, pipeline: SplitterPipeline):
        super().__init__()
        self._pipeline = pipeline
        self._console = Console()

    @property
    def pipeline(self) -> SplitterPipeline:
        return self._pipeline

    @profiled
    def run(self):
        with self._console.status("Processing query...", spinner="dots") as spinner:
            max_retries: int = configs.max_router_retries
            while not self.pipeline.state == States.COMPLETE:
                self.pipeline.track_previous()
                spinner.update(f"[green]{self.pipeline.state.value}[/green]")
                if 0 < max_retries < self.pipeline.failures[self.pipeline.state.value]:
                    spinner.update(f"\nMax state retries reached: {max_retries}")
                    break
                match self.pipeline.state:
                    case States.STARTUP:
                        if self.pipeline.st_startup():
                            self.pipeline.ev_pipeline_started()
                    case States.QUERY_QUEUED:
                        if self.pipeline.st_query_queued():
                            self.pipeline.ev_query_queued()
                    case States.MODEL_SELECT:
                        if self.pipeline.st_model_select():
                            self.pipeline.ev_model_selected()
                    case States.TASK_SPLIT:
                        status, direct = self.pipeline.st_task_split()
                        if status:
                            if direct:
                                self.pipeline.ev_direct_answer()
                            else:
                                self.pipeline.ev_plan_created()
                    case States.EXECUTE_TASK:
                        color, has_next = self.pipeline.st_execute_next()
                        if color.passed:
                            if has_next:
                                self.pipeline.st_execute_next()
                            else:
                                self.pipeline.ev_task_executed()
                    case States.ACCURACY_CHECK:
                        color: AccColor = self.pipeline.st_accuracy_check()
                        if color.passed:
                            self.pipeline.ev_accuracy_passed()
                        else:
                            self.pipeline.ev_accuracy_failed()
                    case States.REFINE_ANSWER:
                        if self.pipeline.st_refine_answer():
                            self.pipeline.ev_answer_refined()
                    case _:
                        spinner.update(f"Error: Machine stopped before it was done ({self.pipeline.state}) %NC%")
                        break
                execution_status: bool = self.pipeline.previous != self.pipeline.state
                execution_status_str: str = (
                    f"{'[green]√[/green]' if execution_status else '[red]X[/red]'}"
                    f" {str(self.pipeline.previous)}"
                )
                self.pipeline.failures[self.pipeline.state.value] += 1 if not execution_status else 0
                self._console.print(f"[green]{execution_status_str}[/green]")

            final_state: States = self.pipeline.state
            final_state_str: str = '[green]√ Succeeded[/green] ' if final_state == States.COMPLETE else '[red]X Failed [/red]'
            self._console.print(f"[cyan]Pipeline Execution {final_state_str} [cyan][{final_state}][/cyan]")

            if final_state != States.COMPLETE:
                self._console.print(f"Failed to generate a response")


if __name__ == '__main__':
    query: str = "What is the size of the moon"
    p: SplitterPipeline = SplitterPipeline(query)
    executor: SplitterExecutor = SplitterExecutor(p)
    executor.start()
    executor.join()
