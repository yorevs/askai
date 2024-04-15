from typing import Optional

from langchain_core.tools import BaseTool

from askai.core.features.tools.terminal import execute_command


class TerminalTool(BaseTool):
    name = "Terminal commands executor"
    description = (
        "Use this tool to run commands directly in various terminal environments. This tool is particularly useful "
        "when other specific tools or features do not meet your requirements. Use this tool also when you haven't "
        "found any other tool that matches the desired action from the user.")

    def _run(self, command: str) -> Optional[str]:
        return execute_command('bash', command)

    def _arun(self, command: str):
        raise NotImplementedError("This tool does not support async")
