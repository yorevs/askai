import json
from operator import itemgetter

from langchain.output_parsers import JsonOutputToolsParser
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def count_emails(last_n_days: int) -> int:
    """Multiply two integers together."""
    return last_n_days * 2


@tool
def send_email(message: str, recipient: str) -> str:
    """Send an email to the recipient."""
    return f"Successfully sent email '{message}' to {recipient}."


@tool
def list_files(path: str) -> str:
    """List the contents of a directory."""
    return f"""
    You list of files in: '{path}'.
       Audio Music Apps/       Music/        Highway-to-Hell.m4a        Opus46.mp3               barbershop.mp3
       Logic Projects/         iTunes/       Last-Kiss.m4a              Thunderstruck.m4a        iTunesMusic
    """


@tool
def analyze_content(text: str) -> str:
    """Analyze the content."""
    return f"""
    Analysing your text: '{text}':

    You have four folders and five music files.
    """


tools = [count_emails, send_email, list_files, analyze_content]
model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0).bind_tools(tools)


def call_tool(tool_invocation: dict) -> Runnable:
    """Function for dynamically constructing the end of the chain based on the model-selected tool."""
    tool_map = {tool.name: tool for tool in tools}
    tool = tool_map[tool_invocation["type"]]
    return RunnablePassthrough.assign(output=itemgetter("args") | tool)


def human_approval(tool_invocations: list) -> list:
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


# .map() allows us to apply a function to a list of inputs.
call_tool_list = RunnableLambda(call_tool).map()
chain = model | JsonOutputToolsParser() | call_tool_list
content = chain.invoke("list my downloads")

call_tool_list = RunnableLambda(call_tool).map()
chain = model | JsonOutputToolsParser() | call_tool_list
print(chain.invoke(f"analyze the content: '{content}'"))
