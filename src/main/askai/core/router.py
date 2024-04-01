import json
import os
from operator import itemgetter
from pathlib import Path
from textwrap import dedent
from typing import Optional, TypeAlias

from hspylib.core.metaclass.singleton import Singleton
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.output_parsers import JsonOutputToolsParser
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough
from langchain_core.runnables.utils import Input, Output
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

RunnableTool: TypeAlias = Runnable[list[Input], list[Output]]


class Router(metaclass=Singleton):
    """TODO"""

    INSTANCE: 'Router' = None

    # PROMPT_DIR: str = str(classpath.resource_path()) + "/assets/prompts/v4"
    PROMPT_DIR: str = '/Users/hjunior/GIT-Repository/GitHub/askai/src/main/askai/resources/assets/prompts/v4'

    @staticmethod
    @tool
    def execute(language: str, command: str) -> str:
        """Execute a command using the specified language.
        :param language: The command language.
        :param command: The command to be executed.
        """
        print(f"Executing '{language}' command: '{command}'")
        return dedent(f"""
        You list of files in: ~/Downloads.
            Audio Music Apps/        Music/         Highway-to-Hell.m4a         Opus46.mp3                barbershop.mp3
            Logic Projects/          iTunes/        Last-Kiss.m4a               Thunderstruck.m4a         iTunesMusic
            The-Trooper.mp3          gift.png       reminder-2023.txt           reminder-2024.txt
        """)

    @staticmethod
    @tool
    def analyze_output(output: str) -> str:
        """Analyze llm outputs.
        :param output: The output to analyze.
        """
        print(f"Analysing the LLM output: '{output}'")
        return dedent(f"""
        Analysing the output: '{output}':

        You have four folders and five music files.
        """)

    @staticmethod
    @tool
    def summarize(paths) -> str:
        """Summarize files and folders."""
        print(f"Summarizing: '{','.join(paths)}'")
        return dedent("""You have 2 tasks to do:
        1. Got to the dentist
        2. Create a project X report.
        """)

    def __init__(self):
        self.tools = [
            Router.execute, Router.analyze_output, Router.summarize
        ]
        self._llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        self._tool = self._llm.bind_tools(self.tools)
        self._context = []

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

    def route(self, *actions: str) -> Optional[str]:
        result: list[RunnableTool] | None = None
        for act in actions:
            # .map() allows us to apply a function to a list of inputs.
            call_tool_list = RunnableLambda(self.call_tool).map()
            chain = self._tool | JsonOutputToolsParser() | call_tool_list
            result: list[RunnableTool] = chain.invoke(f"{act}\n{result}")
        return ' '.join([run['output'] for run in result]) if result else None

    def ask(self, question: str) -> Optional[str]:
        ctx = Path(self.PROMPT_DIR + '/router-prompt.txt').read_text()
        chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
        chain = create_stuff_documents_chain(self._llm, chat_prompt)
        context = Document(ctx)
        response = chain.invoke({"query": question, "context": [context]})
        return self.route(response.split(os.linesep))


assert (router := Router().INSTANCE) is not None

if __name__ == '__main__':
    print(router.ask('list my downloads and analyze the output. If there ia any reminder file, summarize them'))
