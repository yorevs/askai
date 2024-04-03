from functools import lru_cache

from hspylib.core.metaclass.singleton import Singleton
from hspylib.modules.application.exit_status import ExitStatus

from askai.core.askai_configs import configs
from askai.language.argos_translator import ArgosTranslator
from askai.language.language import Language


class AskAiMessages(metaclass=Singleton):
    """Provide access to static 'translated' messages."""

    INSTANCE: "AskAiMessages" = None

    def __init__(self):
        self._translator = ArgosTranslator(Language.EN_US, configs.language)

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
        return self.translate(f"Executing `{command_line}`…")

    @lru_cache
    def cmd_success(self, command_line: str, exit_code: ExitStatus) -> str:
        return self.translate(f"OK, command `{command_line}` executed with {str(exit_code).lower()}")

    @lru_cache
    def searching(self) -> str:
        return self.translate(f"Searching on the internet…")

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

    # Warnings and alerts

    @lru_cache
    def cmd_no_output(self) -> str:
        return self.translate("The command didn't return an output !")

    @lru_cache
    def search_empty(self) -> str:
        return self.translate("The search didn't return an output !")

    @lru_cache
    def access_grant(self) -> str:
        return self.translate("Do you approve executing command on you terminal (yes/[no])?")

    @lru_cache
    def not_a_command(self, shell: str, content: str) -> str:
        return self.translate(f"Reply '{content}' is not a '{shell}' command !")

    @lru_cache
    def invalid_cmd_format(self, output: str) -> str:
        return self.translate(f"Reply '{output}' does not match the correct command format !")

    # Failures

    @lru_cache
    def no_processor(self, query_type: str) -> str:
        return self.translate(f"Error: No suitable processor found for query type: '{query_type}' !")

    @lru_cache
    def invalid_response(self, response_text: str) -> str:
        return self.translate(f"Error: Received an invalid query response/type => '{response_text}' !")

    @lru_cache
    def cmd_no_exist(self, command: str) -> str:
        return self.translate(f"Error: Sorry! Command `{command}' does not exist !")

    @lru_cache
    def cmd_failed(self, cmd_line: str) -> str:
        return self.translate(f"Error: Sorry! Command `{cmd_line}' failed to execute !")

    @lru_cache
    def missing_package(self, err: ImportError) -> str:
        return self.translate(f"Error: Unable to summarize => {str(err)}' !")

    @lru_cache
    def summary_not_possible(self, err: BaseException = None) -> str:
        return self.translate(f"Error: summarization was not possible {'=> ' + str(err) if err else ''}!")

    @lru_cache
    def intelligible(self, question: str) -> str:
        return self.translate(f"Error: Your question '{question}' is not clear, please reformulate !")

    @lru_cache
    def impossible(self, reason: str) -> str:
        return self.translate(f"Error: Impossible to fulfill your request. Reason: {reason} !")

    @lru_cache
    def llm_error(self, error: str) -> str:
        return self.translate(f"Error: 'LLM' failed to reply: {error} !")

    @lru_cache
    def fail_to_search(self, error: str) -> str:
        return self.translate(f"Error: 'InternetSearch' failed: {error} !")


assert (msg := AskAiMessages().INSTANCE) is not None
