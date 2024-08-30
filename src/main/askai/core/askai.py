#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core
      @file: askai.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.__classpath__ import classpath
from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.askai_settings import settings
from askai.core.commander.commander import ask_commander, RE_ASKAI_CMD
from askai.core.component.cache_service import cache, CACHE_DIR
from askai.core.engine.ai_engine import AIEngine
from askai.core.enums.router_mode import RouterMode
from askai.core.features.router.ai_processor import AIProcessor
from askai.core.support.chat_context import ChatContext
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import read_stdin
from askai.exception.exceptions import (ImpossibleQuery, InaccurateResponse, IntelligibleAudioError,
                                        MaxInteractionsReached, TerminatingQuery)
from askai.tui.app_icons import AppIcons
from click import UsageError
from enum import Enum
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import file_is_not_empty, is_debugging
from hspylib.core.zoned_datetime import DATE_FORMAT, now, TIME_FORMAT
from hspylib.modules.application.exit_status import ExitStatus
from hspylib.modules.eventbus.event import Event
from openai import RateLimitError
from pathlib import Path
from typing import List, Optional, TypeAlias

import logging as log
import os
import re
import sys

QueryString: TypeAlias = str | List[str] | None


class AskAi:
    """The AskAI core functionalities."""

    SOURCE_DIR: Path = classpath.source_path()

    RESOURCE_DIR: Path = classpath.resource_path()

    SPLASH: str = classpath.get_resource("splash.txt").read_text(encoding=Charset.UTF_8.val)

    class RunModes(Enum):
        """AskAI run modes"""

        ASKAI_TUI = "ASKAI_TUI"  # Interactive Terminal UI.
        ASKAI_CLI = "ASKAI_CLI"  # Interactive CLI.
        ASKAI_CMD = "ASKAI_CMD"  # Non interactive CLI (Command mode).

    @staticmethod
    def _abort():
        """Abort the execution and exit."""
        sys.exit(ExitStatus.FAILED.val)

    def __init__(
        self,
        interactive: bool,
        speak: bool,
        debug: bool,
        cacheable: bool,
        tempo: int,
        engine_name: str,
        model_name: str,
    ):

        configs.is_interactive = interactive
        configs.is_debug = is_debugging() or debug
        configs.is_speak = speak
        configs.is_cache = cacheable
        configs.tempo = tempo
        configs.engine = engine_name
        configs.model = model_name

        self._session_id = now("%Y%m%d")[:8]
        self._engine: AIEngine = shared.create_engine(engine_name, model_name)
        self._context: ChatContext = shared.create_context(self._engine.ai_token_limit())
        self._console_path = Path(f"{CACHE_DIR}/askai-{self.session_id}.md")
        self._query_prompt: str | None = None
        self._mode: RouterMode = RouterMode.default()

        if not self._console_path.exists():
            self._console_path.touch()

    def __str__(self) -> str:
        return shared.app_info

    @property
    def engine(self) -> AIEngine:
        return self._engine

    @property
    def context(self) -> ChatContext:
        return self._context

    @property
    def mode(self) -> RouterMode:
        return self._mode

    @property
    def query_prompt(self) -> str:
        return self._query_prompt

    @property
    def console_path(self) -> Path:
        return self._console_path

    @property
    def session_id(self) -> str:
        """Get the Session id."""
        return self._session_id

    @property
    def app_settings(self) -> list[tuple[str, ...]]:
        all_settings = [("UUID", "Setting", "Value")]
        for s in settings.settings.search():
            r: tuple[str, ...] = str(s.identity["uuid"]), str(s.name), str(s.value)
            all_settings.append(r)
        return all_settings

    def run(self) -> None:
        """Run the application."""
        ...

    def ask_and_reply(self, question: str) -> tuple[bool, Optional[str]]:
        """Ask the specified question to the AI and provide the reply.
        :param question: The question to ask the AI engine.
        :return: A tuple containing a boolean indicating success or failure, and the AI's reply as an optional string.
        """
        status: bool = True
        output: str | None = None
        processor: AIProcessor = self.mode.processor
        assert isinstance(processor, AIProcessor)

        try:
            if command := re.search(RE_ASKAI_CMD, question):
                args: list[str] = list(
                    filter(lambda a: a and a != "None", re.split(r"\s", f"{command.group(1)} {command.group(2)}"))
                )
                ask_commander(args, standalone_mode=False)
            elif not (output := cache.read_reply(question)):
                log.debug('Response not found for "%s" in cache. Querying from %s.', question, self.engine.nickname())
                events.reply.emit(message=msg.wait(), verbosity="debug")
                output = processor.process(question, context=read_stdin(), query_prompt=self._query_prompt)
                events.reply.emit(message=(output or msg.no_output("processor")))
            else:
                log.debug("Reply found for '%s' in cache.", question)
                events.reply.emit(message=output)
                shared.context.push("HISTORY", question)
                shared.context.push("HISTORY", output, "assistant")
        except (NotImplementedError, ImpossibleQuery) as err:
            events.reply_error.emit(message=str(err))
        except (MaxInteractionsReached, InaccurateResponse) as err:
            events.reply_error.emit(message=msg.unprocessable(str(err)))
        except UsageError as err:
            events.reply_error.emit(message=msg.invalid_command(err))
        except IntelligibleAudioError as err:
            events.reply_error.emit(message=msg.intelligible(err))
        except RateLimitError:
            events.reply_error.emit(message=msg.quote_exceeded())
            status = False
        except TerminatingQuery:
            status = False
        finally:
            if output:
                shared.context.set("LAST_REPLY", output)

        return status, output

    def _create_console_file(self, overwrite: bool = True) -> None:
        """Create a Markdown-formatted console file.
        :param overwrite: Whether to overwrite the existing file if it already exists (default is True).
        """
        is_new: bool = not file_is_not_empty(str(self.console_path)) or overwrite
        with open(self.console_path, "w" if overwrite else "a", encoding=Charset.UTF_8.val) as f_console:
            f_console.write(
                f"{'---' + os.linesep * 2 if not is_new else ''}"
                f"{'# ' + now(DATE_FORMAT) + os.linesep * 2 if is_new else ''}"
                f"## {AppIcons.STARTED} {now(TIME_FORMAT)}\n\n"
            )
            f_console.flush()

    def _reply(self, message: str) -> None:
        """Reply to the user with the AI-generated response.
        :param message: The message to send as a reply to the user.
        """
        ...

    def _reply_error(self, message: str) -> None:
        """Reply to the user with an AI-generated error message or system error.
        :param message: The error message to be displayed to the user.
        """
        ...

    def _cb_mode_changed_event(self, ev: Event) -> None:
        """Callback to handle mode change events.
        :param ev: The event object representing the mode change.
        """
        self._mode: RouterMode = RouterMode.of_name(ev.args.mode)
        if not self._mode.is_default:
            sum_msg: str = (
                f"{msg.enter_qna()} \n"
                f"```\nContext:  {ev.args.sum_path},   {ev.args.glob} \n```\n"
                f"`{msg.press_esc_enter()}` \n\n"
                f"> {msg.qna_welcome()}")
            events.reply.emit(message=sum_msg)
