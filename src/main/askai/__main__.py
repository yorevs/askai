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

from askai.__classpath__ import classpath
from askai.core.askai_configs import configs
from askai.core.enums.run_modes import RunModes
from askai.core.support.shared_instances import LOGGER_NAME
from clitt.core.tui.tui_application import TUIApplication
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import syserr, to_bool
from hspylib.core.tools.dict_tools import get_or_default
from hspylib.core.zoned_datetime import now
from hspylib.modules.application.argparse.parser_action import ParserAction
from hspylib.modules.application.exit_status import ExitStatus
from hspylib.modules.application.version import Version
from textwrap import dedent
from typing import Any, AnyStr, Optional

import click
import logging as log
import os
import re
import sys


class Main(TUIApplication):
    """HomeSetup Ask-AI - Unleash the Power of AI in Your Terminal."""

    # The welcome message
    DESCRIPTION: str = classpath.get_source("welcome.txt").read_text(encoding=Charset.UTF_8.val)

    # Location of the .version file
    VERSION: Version = Version.load(load_dir=classpath.source_path)

    # The resources folder
    RESOURCE_DIR: str = str(classpath.resource_path)

    INSTANCE: "Main"

    @staticmethod
    def setup_logs() -> None:
        """TODO"""
        # FIXME: Move this code to hspylib Application FW
        log.basicConfig(level=log.WARNING)
        logger = log.getLogger(LOGGER_NAME)
        logger.setLevel(log.INFO)
        logger.propagate = False

    def __init__(self, app_name: str):
        super().__init__(app_name, self.VERSION, self.DESCRIPTION.format(self.VERSION), resource_dir=self.RESOURCE_DIR)
        self._askai: Any
        Main.setup_logs()

    @property
    def askai(self) -> Any:
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
                nargs="?") \
            .option(
                "tempo", "t", "tempo",
                "specifies the playback and streaming speed.",
                choices=['1', '2', '3'],
                nargs="?")\
            .option(
                "prompt", "p", "prompt",
                "specifies the landing prompt file (not useful with interactive mode).",
                nargs="?")\
            .option(
                "engine", "e", "engine",
                "specifies which AI engine to use. If not provided, the default engine wil be used.",
                choices=["openai", "gemini"],
                nargs="?")\
            .option(
                "model", "m", "model",
                "specifies which AI model to use (depends on the engine).",
                nargs="?") \
            .option(
                "router", "r", "router",
                "specifies which router mode to use.",
                nargs="?",
                choices=["rag", "chat", "splitter"])
        self._with_arguments() \
            .argument("query_string", "what to ask to the AI engine", nargs="*")
        # fmt: on

    def _main(self, *params, **kwargs) -> ExitStatus:
        """Run the application with the command line arguments.
        :param params: Positional command line arguments.
        :param kwargs: Keyword command line arguments.
        :return: ExitStatus indicating the result of the application run.
        """
        os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
        is_new_ui: bool = to_bool(self._get_argument("ui", False))
        query_string: str | None = self._get_query_string()
        configs.is_interactive = self._get_interactive(query_string)
        if is_new_ui:
            from askai.core.enums.router_mode import RouterMode
            from askai.tui import askai_app

            configs.is_interactive = True  # TUI is always interactive
            os.environ["ASKAI_APP"] = RunModes.ASKAI_TUI.value
            self._askai = askai_app.AskAiApp(
                to_bool(self._get_argument("speak")),
                to_bool(self._get_argument("debug")),
                to_bool(self._get_argument("cache", configs.is_cache)),
                int(self._get_argument("tempo", configs.tempo)),
                self._get_argument("engine", configs.engine),
                self._get_argument("model", configs.model),
                RouterMode.of_name(self._get_mode_str()),
            )
        elif configs.is_interactive or (query_string and not query_string.startswith("/")):
            from askai.core import askai_cli
            from askai.core.enums.router_mode import RouterMode

            os.environ["ASKAI_APP"] = RunModes.ASKAI_CLI.value
            self._askai = askai_cli.AskAiCli(
                to_bool(self._get_argument("speak")),
                to_bool(self._get_argument("debug")),
                to_bool(self._get_argument("cache", configs.is_cache)),
                int(self._get_argument("tempo", configs.tempo)),
                self._get_argument("prompt"),
                self._get_argument("engine", configs.engine),
                self._get_argument("model", configs.model),
                query_string,
                RouterMode.of_name(self._get_mode_str()),
            )
        else:
            os.environ["ASKAI_APP"] = RunModes.ASKAI_CMD.value
            return self._execute_command(query_string)

        log.debug(
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
        """Execute the application main flow.
        :return: The exit status of the application.
        """
        self._askai.run()
        from askai.core.support import shared_instances

        shared_instances.shared.context.save()

        return ExitStatus.SUCCESS

    def _get_argument(self, arg_name: str, default: Any = None) -> Optional[Any]:
        """Get a command line argument, converting to the appropriate type.
        :param arg_name: The name of the command line argument to retrieve.
        :param default: The default value to return if the argument is not found. Defaults to None.
        :return: The value of the argument if found, otherwise the default value.
        """
        if arg := self.get_arg(arg_name) or default:
            if isinstance(arg, str):
                return arg
            elif isinstance(arg, list):
                return get_or_default(arg, 0, "")
            elif isinstance(arg, bool):
                return arg
            elif isinstance(arg, int):
                return arg
            raise TypeError("Argument '%s' has an invalid type: '%s'", arg, type(arg))

        return None

    def _get_query_string(self) -> Optional[str]:
        """Return the query_string parameter.
        :return: The query_string if it exists, otherwise None.
        """
        query_string: str | list[str] = self.get_arg("query_string")
        return query_string if isinstance(query_string, str) else " ".join(query_string)

    def _get_mode_str(self) -> str:
        """Return the router mode according to the specified arguments or from configs.
        :return: The router mode as a string.
        """
        return self._get_argument("router", "default")

    def _get_interactive(self, query_string: str) -> bool:
        """TODO"""
        interactive: bool = to_bool(self._get_argument("interactive", False))
        interactive = interactive if not query_string else False
        return interactive

    def _execute_command(self, command_str: AnyStr) -> ExitStatus:
        """Execute an AskAI-commander command. This method avoids loading all AskAI context and modules.
        :param command_str: The command string to be executed.
        :return: The exit status of the command execution.
        """
        from askai.core.commander import commander

        try:
            if command := re.search(commander.RE_ASKAI_CMD, command_str):
                args: list[str] = list(
                    filter(lambda a: a and a != "None", re.split(r"\s", f"{command.group(1)} {command.group(2)}"))
                )
                commander.ask_commander(args, standalone_mode=False)
            # If no exception is raised, the command executed successfully
            return ExitStatus.SUCCESS
        except click.ClickException as ce:
            ce.show()
            syserr("Command failed due to a ClickException.")
        return ExitStatus.FAILED


# Application entry point
if __name__ == "__main__":
    Main("AskAI").INSTANCE.run(sys.argv[1:])
