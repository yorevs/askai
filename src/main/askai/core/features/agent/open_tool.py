from typing import Optional

from langchain_core.tools import BaseTool

from askai.core.features.tools.terminal import open_command


class OpenTool(BaseTool):
    name = "Open files, folders, and applications"
    description = "Use this tool to open any file, folder, or application on my system."

    def _run(self, pathname: str) -> Optional[str]:
        return open_command(pathname)

    def _arun(self, command: str):
        raise NotImplementedError("This tool does not support async")

