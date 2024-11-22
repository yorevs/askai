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
from askai.core.askai_configs import configs
from askai.core.askai_events import ABORT_EVENT, ASKAI_BUS_NAME, AskAiEvents
from askai.core.askai_messages import msg
from askai.core.enums.acc_color import AccColor
from askai.core.processors.splitter.splitter_pipeline import SplitterPipeline
from askai.core.processors.splitter.splitter_states import States
from askai.core.support.text_formatter import text_formatter as tf
from askai.exception.exceptions import InaccurateResponse
from clitt.core.term.cursor import cursor
from hspylib.core.tools.commons import is_debugging
from hspylib.modules.eventbus.event import Event
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from textwrap import indent
from threading import Thread

import os


class SplitterExecutor(Thread):
    """Responsible for executing a TaskSplitter pipeline."""

    @staticmethod
    def display(text: str, force: bool = False) -> None:
        """Display a debug message if debugging mode is active.
        :param text: The debug message to display
        :param force: Force displaying the message regardless of the debug flag.
        """
        if force or is_debugging():
            tf.console.print(Text.from_markup(text))

    def __init__(self, query: str):
        super().__init__()
        self._pipeline = SplitterPipeline(query)
        self._interrupted = False
        AskAiEvents.bus(ASKAI_BUS_NAME).subscribe(ABORT_EVENT, self.interrupt)

    @property
    def pipeline(self) -> SplitterPipeline:
        return self._pipeline

    def interrupt(self, ev: Event) -> None:
        """Interrupt the active execution pipeline.
        :param ev: The interruption event,
        """
        if self.is_alive():
            self.display(f"[red]{msg.interruption_requested(ev.args.message)} ![/red]", True)
            self._interrupted = True

    def run(self) -> None:
        """Execute the splitter pipeline."""

        try:
            with Live(
                Spinner("dots", f"[green]{self.pipeline.state}…[/green]", style="green"), console=tf.console
            ) as live:
                while not (self._interrupted or self.pipeline.state == States.COMPLETE):
                    self.pipeline.track_previous()
                    if 1 < configs.max_router_retries < 1 + self.pipeline.failures[self.pipeline.state.value]:
                        self.display(f"\n[red] Max retries exceeded: {configs.max_agent_retries}[/red]\n", True)
                        break
                    if 1 < configs.max_iteractions < 1 + self.pipeline.iteractions:
                        self.display(f"\n[red] Max iteractions exceeded: {configs.max_iteractions}[/red]\n", True)
                        break
                    match self.pipeline.state:
                        case States.STARTUP:
                            if self.pipeline.st_startup():
                                self.pipeline.ev_pipeline_started()
                        case States.MODEL_SELECT:
                            if self.pipeline.st_model_select():
                                self.pipeline.ev_model_selected()
                        case States.TASK_SPLIT:
                            if self.pipeline.st_task_split():
                                if self.pipeline.is_direct():
                                    self.display("[yellow]√ Direct answer provided[/yellow]")
                                    self.pipeline.ev_direct_answer()
                                else:
                                    self.display(f"[green]√ Action plan created[/green]")
                                    self.pipeline.ev_plan_created()
                        case States.EXECUTE_TASK:
                            if self.pipeline.st_execute_task():
                                self.pipeline.ev_task_executed()
                        case States.ACC_CHECK:
                            acc_color: AccColor = self.pipeline.st_accuracy_check()
                            c_name: str = acc_color.color.casefold()
                            self.display(f"[green]√ Accuracy check: [{c_name}]{c_name.upper()}[/{c_name}][/green]")
                            if acc_color.passed(AccColor.GOOD):
                                self.pipeline.ev_accuracy_passed()
                            elif acc_color.passed(AccColor.MODERATE):
                                self.pipeline.ev_refine_required()
                            else:
                                self.pipeline.ev_accuracy_failed()
                        case States.REFINE_ANSWER:
                            if self.pipeline.st_refine_answer():
                                self.pipeline.ev_answer_refined()
                        case States.WRAP_ANSWER:
                            if self.pipeline.st_final_answer():
                                self.pipeline.ev_final_answer()
                        case _:
                            self.display(
                                f"[red] Error: Machine halted before complete!({self.pipeline.state})[/red]", True
                            )
                            break

                    execution_status: bool = self.pipeline.previous != self.pipeline.state
                    execution_status_str: str = (
                        f"{'[green]√[/green]' if execution_status else '[red]X[/red]'}"
                        f" {str(self.pipeline.previous)}"
                    )
                    self.pipeline.failures[self.pipeline.state.value] += 1 if not execution_status else 0
                    self.display(f"[green]{execution_status_str}[/green]")
                    live.update(Spinner("dots", f"[green]{self.pipeline.state}…[/green]", style="green"))
                    self.pipeline.iteractions += 1
            cursor.erase_line()
        except InaccurateResponse:
            live.update(Spinner("dots", f"[red]AI failed to respond. Retrying…[/red]", style="green"))

        final_state: States = self.pipeline.state

        if configs.is_debug:
            final_state_str: str = (
                "[green] Succeeded[/green] " if final_state == States.COMPLETE else "[red] Failed [/red]"
            )
            self.display(
                f"\n[cyan]Pipeline execution {final_state_str} [cyan][{final_state}][/cyan] "
                f"after [yellow]{self.pipeline.iteractions}[/yellow] iteractions\n"
            )
            all_failures: str = indent(
                os.linesep.join([f"- {k}: {c}" for k, c in self.pipeline.failures.items()]), "  "
            )
            self.display(f"Failures:\n{all_failures}")

        if final_state != States.COMPLETE and not self._interrupted:
            retries: int = self.pipeline.failures[self.pipeline.state.value]
            self.display(f" Failed to generate a response after {retries} retries", True)
