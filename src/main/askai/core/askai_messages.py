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
from askai.core.askai_configs import configs
from askai.language.argos_translator import ArgosTranslator
from askai.language.language import Language
from functools import cached_property, lru_cache
from hspylib.core.metaclass.singleton import Singleton
from hspylib.modules.application.exit_status import ExitStatus


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

    @lru_cache
    def welcome(self, username: str) -> str:
        return self.translate(f"Welcome back {username.title()}, How can I assist you today ?")

    @lru_cache
    def wait(self) -> str:
        return self.translate("I'm thinking…")

    @lru_cache
    def welcome_back(self) -> str:
        return self.translate("How may I further assist you ?")

    @lru_cache
    def listening(self) -> str:
        return self.translate("I'm listening…")

    @lru_cache
    def transcribing(self) -> str:
        return self.translate("I'm processing your voice…")

    @lru_cache
    def goodbye(self) -> str:
        return self.translate("Goodbye, have a nice day !")

    @lru_cache
    def executing(self, command_line: str) -> str:
        return self.translate(f"> Executing `{command_line}`…")

    @lru_cache
    def cmd_success(self, command_line: str, exit_code: ExitStatus) -> str:
        return self.translate(f"OK, command `{command_line}` executed with {str(exit_code).lower()}")

    @lru_cache
    def searching(self) -> str:
        return self.translate(f"Searching on the internet…")

    @lru_cache
    def scrapping(self) -> str:
        return self.translate(f"Scrapping web site…")

    @lru_cache
    def summarizing(self, path: str) -> str:
        return self.translate(f"Summarizing docs at:'{path}' …")

    @lru_cache
    def enter_qna(self) -> str:
        return self.translate("You have entered the Summarization Q & A")

    @lru_cache
    def leave_qna(self) -> str:
        return self.translate("You have left the Summarization Q & A")

    @lru_cache
    def qna_welcome(self) -> str:
        return self.translate("What specific information are you seeking about the content ?")

    @lru_cache
    def press_esc_enter(self) -> str:
        return self.translate("Press [Esc or Enter] to leave")

    @lru_cache
    def analysis(self, result: str) -> str:
        return self.translate(f"Analysis result: `{result}`")

    @lru_cache
    def assert_acc(self, result: str) -> str:
        return self.translate(f"! Accuracy check: `{result}`")

    @lru_cache
    def action_plan(self, plan_text: str) -> str:
        return self.translate(f"@ Action plan: `{plan_text}`")

    @lru_cache
    def x_reference(self) -> str:
        return self.translate(f"> Looking for **X-References**…")

    @lru_cache
    def describe_image(self, image_path: str) -> str:
        return self.translate(f"Describing image: `{image_path}` …")

    @lru_cache
    def device_switch(self, device_info: str) -> str:
        return self.translate(f"\nSwitching to Audio Input device: `{device_info}`")

    # Warnings and alerts

    @lru_cache
    def search_empty(self) -> str:
        return self.translate("The search didn't return an output !")

    @lru_cache
    def access_grant(self) -> str:
        return self.translate("Do you approve executing this command on you terminal (**yes/[no]**)?")

    # Failures

    @lru_cache
    def no_query_string(self) -> str:
        return self.translate("No query string was provided in non-interactive mode !")

    @lru_cache
    def invalid_response(self, response_text: str) -> str:
        return self.translate(f"Invalid query response/type => '{response_text}' !")

    @lru_cache
    def invalid_command(self, response_text: str) -> str:
        return self.translate(f"Invalid **AskAI** command => '{response_text}' !")

    @lru_cache
    def cmd_no_exist(self, command: str) -> str:
        return self.translate(f"Command `{command}' does not exist !")

    @lru_cache
    def cmd_failed(self, cmd_line: str) -> str:
        return self.translate(f"Command `{cmd_line}' failed to execute !")

    @lru_cache
    def missing_package(self, err: ImportError) -> str:
        return self.translate(f"Unable to summarize => {str(err)}' !")

    @lru_cache
    def summary_not_possible(self, err: BaseException = None) -> str:
        return self.translate(f"summarization was not possible {'=> ' + str(err) if err else ''}!")

    @lru_cache
    def intelligible(self, question: str, reason: str) -> str:
        return self.translate(f"Your question '{question}' is unclear: '{reason}'")

    @lru_cache
    def impossible(self, reason: str) -> str:
        return self.translate(f"Impossible to fulfill your request. Reason: {reason} !")

    @lru_cache
    def llm_error(self, error: str) -> str:
        return self.translate(f"'LLM' failed to reply: {error} !")

    @lru_cache
    def fail_to_search(self, error: str) -> str:
        return self.translate(f"'InternetSearch' failed: {error} !")

    @lru_cache
    def too_many_actions(self) -> str:
        return self.translate("Failed to complete the request => 'Max chained actions reached' !")

    @lru_cache
    def unprocessable(self, reason: str) -> str:
        return self.translate(f"Sorry, I was unable to process your request => '{reason}'")


assert (msg := AskAiMessages().INSTANCE) is not None
