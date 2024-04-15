from typing import Optional

from langchain_core.tools import BaseTool

from askai.core.features.tools.analysis import check_output


class OutputCheckerTool(BaseTool):
    name = "Check for files, folder and applications"
    description = (
        "Use this tool to analyze a command output and check for files, folders and applications. This is often used "
        "after listing the contents of files, folders and applications. The input parameters are the user question and "
        "the content to be analyzed (e.g:. the contents ofa folder listing).")

    def _run(self, question: str, context: str) -> Optional[str]:
        return check_output(question, '')

    def _arun(self, question: str, context: str):
        raise NotImplementedError("This tool does not support async")
