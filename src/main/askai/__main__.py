#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: hspylib
   @package: hspylib
      @file: __main__.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""

import logging as log
import sys
from textwrap import dedent

from clitt.core.tui.tui_application import TUIApplication
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.dict_tools import get_or_default
from hspylib.core.zoned_datetime import now
from hspylib.modules.application.argparse.parser_action import ParserAction
from hspylib.modules.application.exit_status import ExitStatus
from hspylib.modules.application.version import Version

from askai.__classpath__ import _Classpath
from askai.core.askai import AskAi


class Main(TUIApplication):
    """HomeSetup Ask-AI - Unleash the Power of AI in Your Terminal."""

    # The welcome message
    DESCRIPTION = _Classpath.get_source_path("welcome.txt").read_text(encoding=Charset.UTF_8.val)

    # Location of the .version file
    VERSION_DIR = _Classpath.source_path()

    # The resources folder
    RESOURCE_DIR = str(_Classpath.resource_path())

    def __init__(self, app_name: str):
        version = Version.load(load_dir=self.VERSION_DIR)
        super().__init__(app_name, version, self.DESCRIPTION.format(version), resource_dir=self.RESOURCE_DIR)
        self._askai = None

    def _setup_arguments(self) -> None:
        """Initialize application parameters and options."""
        # fmt: off
        self._with_options() \
            .option(
                "engine", "e", "engine",
                "specifies which AI engine to use. If not provided, the default engine wil be used.",
                choices=['openai', 'palm'],
                nargs=1, default='openai')\
            .option(
                "model", "m", "model",
                "specifies which AI model to use (depends on the engine).",
                nargs=1, default='gpt-3.5-turbo')\
            .option(
                "interactive", "i", "interactive",
                "whether you would like to run the program in an interactive mode.",
                nargs="?", action=ParserAction.STORE_TRUE, default=False)\
            .option(
                "quiet", "q", "quiet",
                "whether you want touse speaking (audio in/out).",
                nargs="?", action=ParserAction.STORE_FALSE, default=True)\
            .option(
                "tempo", "t", "tempo",
                "specifies the playback and streaming speed.",
                choices=['1', '2', '3'],
                nargs=1, default='1')
        self._with_arguments() \
            .argument("query_string", "what to ask to the AI engine", nargs="*")
        # fmt: on

    def _main(self, *params, **kwargs) -> ExitStatus:
        """Run the application with the command line arguments."""
        self._askai = AskAi(
            self.get_arg("interactive"),
            self.get_arg("quiet"),
            int(get_or_default(self.get_arg("tempo") or [], 0, "1")),
            self.get_arg("engine"),
            self.get_arg("model"),
            self.get_arg("query_string"),
        )

        log.info(
            dedent(
                f"""
        {self._app_name} v{self._app_version}

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

        return ExitStatus.SUCCESS


# Application entry point
if __name__ == "__main__":
    Main("AskAI").INSTANCE.run(sys.argv[1:])
