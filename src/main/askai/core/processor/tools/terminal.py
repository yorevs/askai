import logging as log
import os
from typing import Optional

from clitt.core.term.cursor import cursor
from clitt.core.term.terminal import Terminal
from hspylib.modules.application.exit_status import ExitStatus
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.tools import tool

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import extract_path


@tool
def terminal(language: str, command_line: str) -> Optional[str]:
    """Execute a terminal command using the specified language.
    :param language: The command language.
    :param command_line: The command line to be executed.
    """
    match language:
        case 'bash':
            return execute_shell(command_line)
        case _:
            raise NotImplemented(f"Language '{language}' is not supported")


def execute_shell(command_line: str) -> Optional[str]:
    """TODO"""

    AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.executing())
    log.info("Executing command `%s'", command_line)
    output, exit_code = Terminal.INSTANCE.shell_exec(command_line, shell=True)

    if exit_code == ExitStatus.SUCCESS:
        log.info("Command succeeded.\nCODE=%s \nPATH: %s \nCMD: %s ", exit_code, os.getcwd(), command_line)
        if _path_ := extract_path(command_line):
            if _path_:
                os.chdir(_path_)
                log.info("Current directory changed to '%s'", _path_)
            else:
                log.warning("Directory '%s' does not exist. Current dir unchanged!", _path_)
        if not output:
            output = msg.cmd_no_output()
        else:
            shared.context.push("CONTEXT", f"\n\nCommand `{command_line}' output:\n```\n{output}```")
            output = process_output(command_line, output)
    else:
        log.error("Command failed.\nCODE=%s \nPATH=%s \nCMD=%s ", exit_code, os.getcwd(), command_line)
        output = msg.cmd_failed(command_line)

    return output


def process_output(command_line: str, command_output: str) -> Optional[str]:
    """Display a command output.
    :param command_line: The command line that produced the output.
    :param command_output: The output to analyze.
    """
    output = None
    template = PromptTemplate(
        input_variables=["command_line", "shell", "idiom", "command_output"],
        template=prompt.read_prompt("output-prompt"))
    final_prompt: str = template.format(
        command_line=command_line, shell=prompt.shell, idiom=shared.idiom)
    log.info("Output::[QUESTION] '%s'  context=%s", final_prompt, command_output)

    chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
    chain = create_stuff_documents_chain(lc_llm.create_chat_model(), chat_prompt)
    context = [Document(command_output)]

    if response := chain.invoke({"query": final_prompt, "context": context}):
        cursor.erase_line()
        log.debug("Output::[RESPONSE] Received from AI: %s.", response)
        shared.context.push("CONTEXT", f"\n\nAI:\n{response}", "assistant")
        output = command_output
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=response)
    else:
        log.error(f"Output processing failed. CONTEXT=%s  RESPONSE=%s", context, response)
        output = msg.llm_error(response)

    return output
