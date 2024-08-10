#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: hspylib
   @package: hspylib
      @file: __main__.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import logging as log
import os
import sys
from textwrap import dedent
from typing import Any, Optional

from askai.__classpath__ import classpath
from askai.core.askai import AskAi
from askai.core.askai_cli import AskAiCli
from askai.core.askai_configs import configs
from askai.core.support.shared_instances import shared
from askai.tui.askai_app import AskAiApp
from clitt.core.term.commons import is_a_tty
from clitt.core.tui.tui_application import TUIApplication
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import to_bool
from hspylib.core.tools.dict_tools import get_or_default
from hspylib.core.zoned_datetime import now
from hspylib.modules.application.argparse.parser_action import ParserAction
from hspylib.modules.application.exit_status import ExitStatus
from hspylib.modules.application.version import Version

if not is_a_tty():
    log.getLogger().setLevel(log.ERROR)


class Main(TUIApplication):
    """HomeSetup Ask-AI - Unleash the Power of AI in Your Terminal."""

    # The welcome message
    DESCRIPTION: str = classpath.get_source("welcome.txt").read_text(encoding=Charset.UTF_8.val)

    # Location of the .version file
    VERSION: Version = Version.load(load_dir=classpath.source_path())

    # The resources folder
    RESOURCE_DIR: str = str(classpath.resource_path())

    INSTANCE: "Main"

    def __init__(self, app_name: str):
        super().__init__(app_name, self.VERSION, self.DESCRIPTION.format(self.VERSION), resource_dir=self.RESOURCE_DIR)
        self._askai: AskAi | AskAiApp

    @property
    def askai(self) -> AskAi | AskAiApp:
        return self._askai

    def _setup_arguments(self) -> None:
        """Initialize application parameters and options."""

        # fmt: off
        self._with_options() \
            .option(
                "interactive", "i", "interactive",
                "whether you would like to run the program in an interactive mode.",
                nargs="?", action=ParserAction.STORE_TRUE)\
            .option(
                "speak", "s", "speak",
                "whether you want the AI to speak (audio out TTS).",
                nargs="?", action=ParserAction.STORE_TRUE)\
            .option(
                "debug", "d", "debug",
                "whether you want to run under debug mode.",
                nargs="?", action=ParserAction.STORE_TRUE) \
            .option(
                "ui", "u", "ui",
                "whether to use the new AskAI TUI (experimental).",
                nargs="?", action=ParserAction.STORE_TRUE)\
            .option(
                "cache", "c", "cache",
                "whether you want to cache AI replies.",
                nargs="?", default=True) \
            .option(
                "tempo", "t", "tempo",
                "specifies the playback and streaming speed.",
                choices=['1', '2', '3'],
                nargs="?")\
            .option(
                "prompt", "p", "prompt",
                "specifies the query prompt file (not useful with interactive mode).",
                nargs="?")\
            .option(
                "engine", "e", "engine",
                "specifies which AI engine to use. If not provided, the default engine wil be used.",
                choices=["openai", "gemini"],
                nargs="?")\
            .option(
                "model", "m", "model",
                "specifies which AI model to use (depends on the engine).",
                nargs="?")
        self._with_arguments() \
            .argument("query_string", "what to ask to the AI engine", nargs="*")
        # fmt: on

    def _main(self, *params, **kwargs) -> ExitStatus:
        """Run the application with the command line arguments."""
        is_new_ui: bool = to_bool(self._get_argument("ui", False))
        if not is_new_ui:
            interactive: bool = to_bool(self._get_argument("interactive", False))
            self._askai = AskAiCli(
                interactive,
                to_bool(self._get_argument("speak")),
                to_bool(self._get_argument("debug")),
                to_bool(self._get_argument("cache", configs.is_cache)),
                int(self._get_argument("tempo", configs.tempo)),
                self._get_argument("prompt"),
                self._get_argument("engine", configs.engine),
                self._get_argument("model", configs.model),
                self._get_query_string(),
            )
        else:
            self._askai = AskAiApp(
                to_bool(self._get_argument("speak")),
                to_bool(self._get_argument("debug")),
                to_bool(self._get_argument("cache", configs.is_cache)),
                int(self._get_argument("tempo", configs.tempo)),
                self._get_argument("engine", configs.engine),
                self._get_argument("model", configs.model),
            )

        log.info(
            dedent(
                f"""
        {os.environ.get("ASKAI_APP")} v{self._app_version}

        Settings ==============================
                STARTED: {now("%Y-%m-%d %H:%M:%S")}
        {self.configs}
        """
            )
        )
        return self._exec_application()

    def _exec_application(self) -> ExitStatus:
        """Execute the application main flow."""
        self._askai.run()
        shared.context.save()

        return ExitStatus.SUCCESS

    def _get_argument(self, arg_name: str, default: Any = None) -> Optional[Any]:
        """Get a command line argument, converting to the appropriate type."""
        if arg := self.get_arg(arg_name) or default:
            if isinstance(arg, str):
                return arg
            elif isinstance(arg, list):
                return get_or_default(arg, 0, "")
            elif isinstance(arg, bool):
                return arg
            elif isinstance(arg, int):
                return arg
            else:
                raise TypeError("Argument '%s' has an invalid type: '%s'", arg, type(arg))

        return None

    def _get_query_string(self) -> Optional[str]:
        """Return the query_string parameter."""
        query_string: str | list[str] = self.get_arg("query_string")
        return query_string if isinstance(query_string, str) else " ".join(query_string)


# Application entry point
if __name__ == "__main__":
    Main("AskAI").INSTANCE.run(sys.argv[1:])
