from functools import lru_cache

from hspylib.core.metaclass.singleton import Singleton
from hspylib.modules.application.exit_status import ExitStatus

from askai.core.askai_configs import configs
from askai.language.argos_translator import ArgosTranslator
from askai.language.language import Language


class AskAiMessages(metaclass=Singleton):
    """Provide access to static 'translated' messages."""

    INSTANCE: 'AskAiMessages' = None

    def __init__(self):
        self._translator = ArgosTranslator(Language.EN_US, configs.language)

    @lru_cache
    def translate(self, text: str) -> str:
        """Translate text using the configured language."""
        return self._translator.translate(text)

    # Informational

    @lru_cache
    def welcome(self, username: str) -> str:
        return self.translate(f"Hello {username.title()}, How can I assist you today?")

    @lru_cache
    def wait(self) -> str:
        return self.translate(f"I'm thinking, please wait…")

    @lru_cache
    def listening(self) -> str:
        return self.translate(f"I'm listening…")

    @lru_cache
    def noise_levels(self) -> str:
        return self.translate(f"Adjusting noise levels…")

    @lru_cache
    def transcribing(self) -> str:
        return self.translate(f"I'm processing your voice, please wait…")

    @lru_cache
    def goodbye(self) -> str:
        return self.translate(f"Goodbye, have a nice day ! ")

    @lru_cache
    def executing(self, cmd_line: str) -> str:
        return self.translate(f"Executing command `{cmd_line}', please wait…")

    @lru_cache
    def cmd_success(self, exit_code: ExitStatus) -> str:
        return self.translate(f"OK, command executed with {str(exit_code).lower()}")

    @lru_cache
    def summarized_output(self) -> str:
        return self.translate("Here is a summarized version of the command output: \n\n")

    @lru_cache
    def analysis_output(self) -> str:
        return self.translate("Analysing the provided command output: \n\n")

    # Warnings and alerts

    @lru_cache
    def cmd_no_output(self) -> str:
        return self.translate(f"The command didn't return an output !")

    @lru_cache
    def access_grant(self) -> str:
        return self.translate(f"AskAI requires access to your files, folders and apps. Continue (yes/[no])?")

    @lru_cache
    def not_a_command(self, shell: str, content: str) -> str:
        return self.translate(f"Returned context '{content}' is not a '{shell}' command!")

    @lru_cache
    def invalid_cmd_format(self, output: str) -> str:
        return self.translate(f"Returned command output '{output}' does not match the correct format!")

    # Failures

    @lru_cache
    def invalid_response(self, response_text: str) -> str:
        return self.translate(f"Received an invalid query response/type '{response_text}' !")

    @lru_cache
    def cmd_no_exist(self, command: str) -> str:
        return self.translate(f"Sorry! Command `{command}' does not exist !")

    @lru_cache
    def cmd_failed(self, cmd_line: str) -> str:
        return self.translate(f"Sorry! Command `{cmd_line}' failed to execute !")

    @lru_cache
    def intelligible(self) -> str:
        return self.translate(f"Your question is not clear, please rephrase!")

    @lru_cache
    def llm_error(self, error: str) -> str:
        return self.translate(f"LLM returned an error: {error}")


assert (msg := AskAiMessages().INSTANCE) is not None
