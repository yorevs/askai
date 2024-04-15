from typing import Optional

from langchain_core.tools import BaseTool

from askai.core.features.tools.terminal import list_contents


class ListTool(BaseTool):
    name = "List folder contents"
    description = (
        "This feature is designed for retrieving and displaying the contents of a specified folder. It is useful for "
        "quickly assessing the files and subdirectories within any directory. The input parameter is the folder you "
        "want to list .")

    def _run(self, folder: str) -> Optional[str]:
        return list_contents(folder)

    def _arun(self, folder: str):
        raise NotImplementedError("This tool does not support async")
