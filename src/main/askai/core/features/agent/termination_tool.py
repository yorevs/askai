from typing import Optional

from langchain_core.tools import BaseTool

from askai.exception.exceptions import TerminatingQuery


class TerminationTool(BaseTool):
    name = "Terminating Intention Handler"
    description = (
        "Use this tool when the user decides to conclude the interaction. This function ensures a"
        "smooth and clear ending to the session, confirming user intent to terminate the dialogue. The reason message "
        "should be passed when invoking this tool.")

    def _run(self, reason_message: str) -> Optional[str]:
        return str(TerminatingQuery(reason_message))

    def _arun(self, case: str):
        raise NotImplementedError("This tool does not support async")
