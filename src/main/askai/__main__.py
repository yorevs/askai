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

import typing
import logging as log
import os
import re
import sys

from clitt.core.tui.tui_application import TUIApplication
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import syserr, to_bool
from hspylib.modules.application.argparse.parser_action import ParserAction
from hspylib.modules.application.exit_status import ExitStatus
from hspylib.modules.application.version import Version

from askai.__classpath__ import classpath
from askai.core.support.utilities import QueryString


class Main(TUIApplication):
    """HomeSetup Ask-AI - Unleash the Power of AI in Your Terminal."""

    # The welcome message
    DESCRIPTION: str = classpath.get_source("welcome.txt").read_text(encoding=Charset.UTF_8.val)

    # Location of the .version file
    VERSION: Version = Version.load(load_dir=classpath.source_path)

    # The resources folder
    RESOURCE_DIR: str = str(classpath.resource_path)

    # Singleton instance
    INSTANCE: "Main"

    @staticmethod
    def _execute_command(command_str: typing.AnyStr) -> ExitStatus:
        """Execute an AskAI-commander command. This method avoids loading all AskAI context and modules.
        :param command_str: The command string to be executed.
        :return: The exit status of the command execution.
        """
        import click
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

    def __init__(self, app_name: str):
        super().__init__(app_name, self.VERSION, self.DESCRIPTION.format(self.VERSION), resource_dir=self.RESOURCE_DIR)
        self._askai: typing.Any

    @property
    def askai(self) -> typing.Any:
        return self._askai

    def _setup_arguments(self) -> None:
        """Initialize application parameters and options."""

        # fmt: off
        self._with_options() \
            .option(
                "interactive", "i", "interactive",
                "Whether you would like to run the program in interactive mode.",
                nargs="?", action=ParserAction.STORE_TRUE)\
            .option(
                "speak", "s", "speak",
                "Whether you want the AI to speak (audio out TTS).",
                nargs="?", action=ParserAction.STORE_TRUE)\
            .option(
                "debug", "d", "debug",
                "Whether you want to run under debug mode.",
                nargs="?", action=ParserAction.STORE_TRUE) \
            .option(
                "ui", "u", "ui",
                "Whether to use the new AskAI TUI (experimental).",
                nargs="?", action=ParserAction.STORE_TRUE)\
            .option(
                "cache", "c", "cache",
                "Whether you want to cache AI replies.",
                nargs="?") \
            .option(
                "tempo", "t", "tempo",
                "Set the playback and streaming speed.",
                choices=['1', '2', '3'],
                nargs="?")\
            .option(
                "prompt", "p", "prompt",
                "Set the landing prompt file (not useful with interactive mode).",
                nargs="?")\
            .option(
                "engine", "e", "engine",
                "Set which AI engine to use (if not provided, the default engine wil be used).",
                choices=["openai", "gemini", "llama"],
                nargs="?")\
            .option(
                "model", "m", "model",
                "Set which AI-Engine model to use (depends on the engine).",
                nargs="?") \
            .option(
                "router", "r", "router",
                "Set which router mode to use.",
                nargs="?",
                choices=["rag", "chat", "splitter"])
        self._with_arguments() \
            .argument(
                "query_string", "What to ask the AI engine",
                nargs="*")
        # fmt: on

    def _main(self, *params, **kwargs) -> ExitStatus:
        """Run the application with the command line arguments.
        :param params: Positional command line arguments.
        :param kwargs: Keyword command line arguments.
        :return: ExitStatus indicating the result of the application run.
        """
        from askai.core.askai_configs import configs
        from askai.core.enums.run_modes import RunModes
        from hspylib.core.zoned_datetime import now
        from textwrap import dedent

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

        # fmt: off
        log.debug(dedent(f"""\
        {os.environ.get("ASKAI_APP")} v{self._app_version}

        Application Settings ==============================
                STARTED: {now("%Y-%m-%d %H:%M:%S")}
        {self.configs}
        """))
        # fmt: on
        return self._exec_application()

    def _exec_application(self) -> ExitStatus:
        """Execute the application main flow.
        :return: The exit status of the application.
        """
        self._askai.run()
        from askai.core.support import shared_instances

        shared_instances.shared.context.save()

        return ExitStatus.SUCCESS

    def _get_argument(self, arg_name: str, default: typing.Any = None) -> typing.Optional[typing.Any]:
        """Get a command line argument, converting to the appropriate type.
        :param arg_name: The name of the command line argument to retrieve.
        :param default: The default value to return if the argument is not found. Defaults to None.
        :return: The value of the argument if found, otherwise the default value.
        """
        if arg := self.get_arg(arg_name) or default:
            if isinstance(arg, str):
                return arg
            elif isinstance(arg, list):
                return " ".join(arg)
            elif isinstance(arg, bool):
                return arg
            elif isinstance(arg, int):
                return arg
            raise TypeError("Argument '%s' has an invalid type: '%s'", arg, type(arg))

        return None

    def _get_query_string(self) -> typing.Optional[str]:
        """Return the query_string parameter.
        :return: The query_string if it exists, None otherwise.
        """
        query_string: QueryString = self._get_argument("query_string")
        return " ".join(query_string) if isinstance(query_string, list) else query_string

    def _get_mode_str(self) -> str:
        """Return the router mode according to the specified arguments or from configs.
        :return: The router mode as a string.
        """
        return self._get_argument("router", "default")

    def _get_interactive(self, query_string: str) -> bool:
        """Return the interactive parameter if query_string is not specified; False otherwise.
        :param query_string: The query string to check for interactivity.
        :return: The value of the interactive parameter or False based on query_string presence.
        """
        return to_bool(self._get_argument("interactive", not query_string))


# Application entry point
if __name__ == "__main__":
    Main("AskAI").INSTANCE.run(sys.argv[1:])
