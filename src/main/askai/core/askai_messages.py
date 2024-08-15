#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.askai_messages
      @file: askai_messages.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import re
from functools import cached_property, lru_cache

from hspylib.core.metaclass.singleton import Singleton

from askai.core.askai_configs import configs
from askai.language.ai_translator import AITranslator
from askai.language.language import Language
from askai.language.translators.marian import MarianTranslator


class AskAiMessages(metaclass=Singleton):
    """Provide access to static 'translated' messages."""

    INSTANCE: "AskAiMessages"

    TRANSLATOR: AITranslator = MarianTranslator

    @staticmethod
    @lru_cache
    def get_translator(from_lang: Language, to_lang: Language) -> AITranslator:
        return AskAiMessages.TRANSLATOR(from_lang, to_lang)

    def __init__(self):
        # fmt: off
        self._accurate_responses: list[str] = [
            self.welcome_back()
        ]
        # fmt: on

    @cached_property
    def accurate_responses(self) -> list[str]:
        return self._accurate_responses

    @property
    def translator(self) -> AITranslator:
        return AskAiMessages.get_translator(Language.EN_US, configs.language)

    @lru_cache(maxsize=256)
    def translate(self, text: str) -> str:
        """Translate text using the configured language."""
        # Avoid translating debug messages.
        if re.match(r'^~~\[DEBUG]~~.*', text, flags=re.IGNORECASE | re.MULTILINE):
            return text
        return self.translator.translate(text)

    # Informational

    def welcome(self, username: str) -> str:
        return f"Welcome back {username}, How can I assist you today ?"

    def wait(self) -> str:
        return "I'm thinking…"

    def welcome_back(self) -> str:
        return "How may I further assist you ?"

    def listening(self) -> str:
        return "I'm listening…"

    def transcribing(self) -> str:
        return "I'm processing your voice…"

    def goodbye(self) -> str:
        return "Goodbye, have a nice day !"

    def smile(self, countdown: int) -> str:
        return f"\nSmile {str(countdown)} "

    def cmd_success(self, command_line: str) -> str:
        return f"OK, command `{command_line}` succeeded"

    def searching(self) -> str:
        return f"Searching on the internet…"

    def scrapping(self) -> str:
        return f"Scrapping web site…"

    def summarizing(self, path: str) -> str:
        return f"Summarizing docs at:'{path}'…"

    def summary_succeeded(self, path: str, glob: str) -> str:
        return f"Summarization of docs at: **{path}/{glob}** succeeded !"

    def enter_qna(self) -> str:
        return "You have *entered* the **Summarization Q & A**"

    def leave_qna(self) -> str:
        return "You have *left* the **Summarization Q & A**"

    def leave_rag(self) -> str:
        return "You have *left* the **RAG Mode**"

    def qna_welcome(self) -> str:
        return "  What specific information are you seeking about this content ?"

    def press_esc_enter(self) -> str:
        return "Type [exit] to exit Q & A mode"

    def device_switch(self, device_info: str) -> str:
        return f"\nSwitching to Audio Input device: `{device_info}`\n"

    def photo_captured(self, photo: str) -> str:
        return f"~~[DEBUG]~~ WebCam photo captured: `{photo}`"

    def executing(self, command_line: str) -> str:
        return f"~~[DEBUG]~~ Executing: `{command_line}`…"

    # Debug messages

    def analysis(self, result: str) -> str:
        return f"~~[DEBUG]~~ Analysis result => {result}"

    def assert_acc(self, status: str, details: str) -> str:
        match status.casefold():
            case 'red':
                cl = '~~'
            case 'yellow':
                cl = '`'
            case 'green':
                cl = '*'
            case _:
                cl = ''
        return f"~~[DEBUG]~~ Accuracy result => {cl}{status}:{cl} {details}"

    def action_plan(self, plan_text: str) -> str:
        return f"~~[DEBUG]~~ Action plan > {plan_text}"

    def x_reference(self, pathname: str) -> str:
        return f"~~[DEBUG]~~ Resolving X-References: `{pathname}`…"

    def describe_image(self, image_path: str) -> str:
        return f"~~[DEBUG]~~ Describing image: `{image_path}`…"

    def model_select(self, model: str) -> str:
        return f"~~[DEBUG]~~ Using routing model: `{model}`"

    def task(self, task: str) -> str:
        return f"~~[DEBUG]~~ > `Task:` {task}"

    def final_query(self, query: str) -> str:
        return f"~~[DEBUG]~~ > Final query: `{query}`"

    def no_caption(self) -> str:
        return "No caption available"

    # Warnings and alerts

    def no_output(self, source: str) -> str:
        return f"The {source} didn't produce an output !"

    def access_grant(self) -> str:
        return "Do you approve executing this command on you terminal (~~yes/[no]~~)?"

    # Failures

    def no_query_string(self) -> str:
        return "No query string was provided in non-interactive mode !"

    def invalid_response(self, response_text: str) -> str:
        return f"Invalid query response/type => '{response_text}' !"

    def invalid_command(self, response_text: str) -> str:
        return f"Invalid **AskAI** command => '{response_text}' !"

    def cmd_no_exist(self, command: str) -> str:
        return f"Command: `{command}' does not exist !"

    def cmd_failed(self, cmd_line: str) -> str:
        return f"Command: `{cmd_line}' failed to execute !"

    def camera_not_open(self) -> str:
        return "Camera is not open, or unauthorized!"

    def missing_package(self, err: ImportError) -> str:
        return f"Unable to summarize => {str(err)}' !"

    def summary_not_possible(self, err: BaseException = None) -> str:
        return f"Summarization was not possible {'=> ' + str(err) if err else ''}!"

    def intelligible(self, reason: str) -> str:
        return f"Your speech was not intelligible => '{reason}' !"

    def impossible(self, reason: str) -> str:
        return f"Impossible to fulfill your request => `{reason}` !"

    def timeout(self, reason: str) -> str:
        return f"Time out while {reason} !"

    def llm_error(self, error: str) -> str:
        return f"**LLM** failed to reply: {error} !"

    def fail_to_search(self, error: str) -> str:
        return f"'Internet Search' failed: {error} !"

    def too_many_actions(self) -> str:
        return "Failed to complete the request => 'Max chained actions reached' !"

    def unprocessable(self, reason: str) -> str:
        return f"Sorry, {reason}"

    def quote_exceeded(self) -> str:
        return(
            f"Oops! Looks like you have reached your quota limit. You can add credits at: "
            f"https://platform.openai.com/settings/organization/billing/overview")


assert (msg := AskAiMessages().INSTANCE) is not None
