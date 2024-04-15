from typing import Optional

from langchain_core.tools import BaseTool

from askai.exception.exceptions import UnintelligibleQuery


class UnintelligibleTool(BaseTool):
    name = "Unintelligible Question Handler"
    description = (
        "Use this tool when a user's question is unclear, difficult or impossible to comprehend. "
        "This tool takes as a param the user's question.")

    def _run(self, question: str) -> Optional[str]:
        return str(UnintelligibleQuery(question))

    def _arun(self, question: str):
        raise NotImplementedError("This tool does not support async")
