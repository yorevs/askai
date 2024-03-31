import json
from operator import itemgetter
from typing import Optional, TypeAlias

from hspylib.core.metaclass.singleton import Singleton
from langchain.output_parsers import JsonOutputToolsParser
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough
from langchain_core.runnables.utils import Input, Output
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


RunnableTool: TypeAlias = Runnable[list[Input], list[Output]]


class Router(metaclass=Singleton):
    """TODO"""

    INSTANCE: 'Router' = None

    @staticmethod
    @tool
    def count_emails(last_n_days: int) -> int:
        """Multiply two integers together."""
        return last_n_days * 2

    @staticmethod
    @tool
    def send_email(message: str, recipient: str) -> str:
        """Send an email to the recipient."""
        return f"Successfully sent email '{message}' to {recipient}."

    @staticmethod
    @tool
    def list_files(path: str) -> str:
        """List the contents of a directory."""
        return f"""
        You list of files in: '{path}'.
            Audio Music Apps/        Music/         Highway-to-Hell.m4a         Opus46.mp3                barbershop.mp3
            Logic Projects/          iTunes/        Last-Kiss.m4a               Thunderstruck.m4a         iTunesMusic
        """

    @staticmethod
    @tool
    def analyze_output(text: str) -> str:
        """Analyze llm outputs."""
        return f"""
        Analysing your text: '{text}':

        You have four folders and five music files.
        """

    def __init__(self):
        self.tools = [
            Router.count_emails, Router.send_email, Router.list_files, Router.analyze_output
        ]
        self.model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0).bind_tools(self.tools)

    def call_tool(self, tool_invocation: dict) -> Runnable:
        """Function for dynamically constructing the end of the chain based on the model-selected tool."""
        tool_map = {tool.name: tool for tool in self.tools}
        tool = tool_map[tool_invocation["type"]]
        return RunnablePassthrough.assign(output=itemgetter("args") | tool)

    def human_approval(self, tool_invocations: list) -> list:
        tool_strs = "\n\n".join(
            json.dumps(tool_call, indent=2) for tool_call in tool_invocations
        )
        msg = (
            f"Do you approve of the following tool invocations\n\n{tool_strs}\n\n"
            "Anything except 'Y'/'Yes' (case-insensitive) will be treated as a no."
        )
        resp = input(msg)
        if resp.lower() not in ("yes", "y"):
            raise ValueError(f"Tool invocations not approved:\n\n{tool_strs}")
        return tool_invocations

    def ask(self, *questions: str) -> Optional[str]:
        result: list[RunnableTool] | None = None
        for q in questions:
            # .map() allows us to apply a function to a list of inputs.
            call_tool_list = RunnableLambda(self.call_tool).map()
            chain = self.model | JsonOutputToolsParser() | call_tool_list
            result: list[RunnableTool] = chain.invoke(f"{q} {result}")
        return ' '.join([r['output'] for r in result]) if result else None


assert (router := Router().INSTANCE) is not None

if __name__ == '__main__':
    print(router.ask('list my downloads', 'analyze the output'))
