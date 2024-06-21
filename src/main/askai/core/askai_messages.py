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
from functools import cached_property, lru_cache

from askai.core.askai_configs import configs
from askai.language.argos_translator import ArgosTranslator
from askai.language.language import Language
from hspylib.core.metaclass.singleton import Singleton


class AskAiMessages(metaclass=Singleton):
    """Provide access to static 'translated' messages."""

    INSTANCE: "AskAiMessages"

    def __init__(self):
        self._translator = ArgosTranslator(Language.EN_US, configs.language)
        self._accurate_responses: list[str] = [self.welcome_back()]

    @cached_property
    def accurate_responses(self) -> list[str]:
        return self._accurate_responses

    @lru_cache
    def translate(self, text: str) -> str:
        """Translate text using the configured language."""
        return self._translator.translate(text)

    # Informational

    @lru_cache(maxsize=1)
    def welcome(self, username: str) -> str:
        return self.translate(f"Welcome back {username.title()}, How can I assist you today ?")

    @lru_cache(maxsize=1)
    def wait(self) -> str:
        return self.translate("I'm thinking…")

    @lru_cache(maxsize=1)
    def welcome_back(self) -> str:
        return self.translate("How may I further assist you ?")

    @lru_cache(maxsize=1)
    def listening(self) -> str:
        return self.translate("I'm listening…")

    @lru_cache(maxsize=1)
    def transcribing(self) -> str:
        return self.translate("I'm processing your voice…")

    @lru_cache(maxsize=1)
    def goodbye(self) -> str:
        return self.translate("Goodbye, have a nice day !")

    @lru_cache(maxsize=1)
    def executing(self, command_line: str) -> str:
        return self.translate(f"~~[DEBUG]~~ Executing: `{command_line}`…")

    @lru_cache(maxsize=1)
    def cmd_success(self, command_line: str) -> str:
        return self.translate(f"OK, command `{command_line}` succeeded")

    @lru_cache(maxsize=1)
    def searching(self) -> str:
        return self.translate(f"Searching on the internet…")

    @lru_cache(maxsize=1)
    def scrapping(self) -> str:
        return self.translate(f"Scrapping web site…")

    @lru_cache(maxsize=1)
    def summarizing(self, path: str) -> str:
        return self.translate(f"Summarizing docs at:'{path}'…")

    @lru_cache(maxsize=1)
    def enter_qna(self) -> str:
        return self.translate("You have entered the Summarization Q & A")

    @lru_cache(maxsize=1)
    def leave_qna(self) -> str:
        return self.translate("You have left the Summarization Q & A")

    @lru_cache(maxsize=1)
    def qna_welcome(self) -> str:
        return self.translate("What specific information are you seeking about the content ?")

    @lru_cache(maxsize=1)
    def press_esc_enter(self) -> str:
        return self.translate("Press [Esc or Enter] to leave")

    @lru_cache(maxsize=1)
    def analysis(self, result: str) -> str:
        return self.translate(f"~~[DEBUG]~~ Analysis result => {result}")

    @lru_cache(maxsize=1)
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
        return self.translate(f"~~[DEBUG]~~ Accuracy result => {cl}{status}:{cl} {details}")

    @lru_cache(maxsize=1)
    def action_plan(self, plan_text: str) -> str:
        return self.translate(f"~~[DEBUG]~~ Action plan => {plan_text}")

    @lru_cache(maxsize=1)
    def x_reference(self, pathname: str) -> str:
        return self.translate(f"~~[DEBUG]~~ Resolving X-References: `{pathname}`…")

    @lru_cache(maxsize=1)
    def describe_image(self, image_path: str) -> str:
        return self.translate(f"~~[DEBUG]~~ Describing image: `{image_path}`…")

    @lru_cache(maxsize=1)
    def model_select(self, model: str) -> str:
        return self.translate(f"~~[DEBUG]~~ Using routing model: `{model}`")

    @lru_cache(maxsize=1)
    def device_switch(self, device_info: str) -> str:
        return self.translate(f"\nSwitching to Audio Input device: `{device_info.strip()}`\n")

    # Warnings and alerts

    @lru_cache(maxsize=1)
    def no_output(self, source: str) -> str:
        return self.translate(f"The {source} didn't produce an output !")

    @lru_cache(maxsize=1)
    def access_grant(self) -> str:
        return self.translate("Do you approve executing this command on you terminal (~~yes/[no]~~)?")

    # Failures

    @lru_cache(maxsize=1)
    def no_query_string(self) -> str:
        return self.translate("No query string was provided in non-interactive mode !")

    @lru_cache(maxsize=1)
    def invalid_response(self, response_text: str) -> str:
        return self.translate(f"Invalid query response/type => '{response_text}' !")

    @lru_cache(maxsize=1)
    def invalid_command(self, response_text: str) -> str:
        return self.translate(f"Invalid **AskAI** command => '{response_text}' !")

    @lru_cache(maxsize=1)
    def cmd_no_exist(self, command: str) -> str:
        return self.translate(f"Command: `{command}' does not exist !")

    @lru_cache(maxsize=1)
    def cmd_failed(self, cmd_line: str) -> str:
        return self.translate(f"Command: `{cmd_line}' failed to execute !")

    @lru_cache(maxsize=1)
    def missing_package(self, err: ImportError) -> str:
        return self.translate(f"Unable to summarize => {str(err)}' !")

    @lru_cache(maxsize=1)
    def summary_not_possible(self, err: BaseException = None) -> str:
        return self.translate(f"Summarization was not possible {'=> ' + str(err) if err else ''}!")

    @lru_cache(maxsize=1)
    def intelligible(self, reason: str) -> str:
        return self.translate(f"Your speech was not intelligible => '{reason}' !")

    @lru_cache(maxsize=1)
    def impossible(self, reason: str) -> str:
        return self.translate(f"Impossible to fulfill your request => `{reason}` !")

    @lru_cache(maxsize=1)
    def timeout(self, reason: str) -> str:
        return self.translate(f"Time out while {reason} !")

    @lru_cache(maxsize=1)
    def llm_error(self, error: str) -> str:
        return self.translate(f"**LLM** failed to reply: {error} !")

    @lru_cache(maxsize=1)
    def fail_to_search(self, error: str) -> str:
        return self.translate(f"'Internet Search' failed: {error} !")

    @lru_cache(maxsize=1)
    def too_many_actions(self) -> str:
        return self.translate("Failed to complete the request => 'Max chained actions reached' !")

    @lru_cache(maxsize=1)
    def unprocessable(self, reason: str) -> str:
        return self.translate(f"Sorry, {reason}")

    @lru_cache(maxsize=1)
    def quote_exceeded(self) -> str:
        return self.translate(
            f"Oops! Looks like you have reached your quota limit. You can add credits at: "
            f"https://platform.openai.com/settings/organization/billing/overview")


assert (msg := AskAiMessages().INSTANCE) is not None
