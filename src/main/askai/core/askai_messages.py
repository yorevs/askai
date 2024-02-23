from functools import lru_cache

from hspylib.core.metaclass.singleton import Singleton
from hspylib.modules.application.exit_status import ExitStatus

from askai.core.askai_configs import AskAiConfigs
from askai.language.argos_translator import ArgosTranslator
from askai.language.language import Language


class AskAiMessages(metaclass=Singleton):
    """Provide access to static 'translated' messages."""

    INSTANCE = None

    def __init__(self):
        self._configs: AskAiConfigs = AskAiConfigs.INSTANCE
        self._translator = ArgosTranslator.INSTANCE or ArgosTranslator(Language.EN_US, self._configs.language)
        self.llm = "%EL0% AskAI"

    @lru_cache
    def welcome(self, username: str) -> str:
        return self.translate(f"Hello {username.title()}, How can I assist you today?")

    @lru_cache
    def wait(self) -> str:
        return self.translate(f"I'm thinking, please wait.")

    @lru_cache
    def listening(self) -> str:
        return self.translate(f"{self.llm}: I'm listening.")

    @lru_cache
    def noise_levels(self) -> str:
        return self.translate(f"{self.llm}: Adjusting noise levels.")

    @lru_cache
    def transcribing(self) -> str:
        return self.translate(f"{self.llm}: Processing your voice, please wait.")

    @lru_cache
    def goodbye(self) -> str:
        return self.translate(f"Goodbye, have a nice day ! ")

    @lru_cache
    def executing(self) -> str:
        return self.translate(f"Executing command, please wait.")

    @lru_cache
    def cmd_success(self, exit_code: ExitStatus) -> str:
        return self.translate(f"OK, the command returned with code: {exit_code}")

    @lru_cache
    def cmd_no_output(self) -> str:
        return self.translate(f"The command didn't return an output !")

    @lru_cache
    def cmd_no_exist(self, command: str) -> str:
        return self.translate(f"Sorry! Command `{command}' does not exist !")

    @lru_cache
    def cmd_failed(self, cmd_line: str) -> str:
        return self.translate(f"Sorry! Command `{cmd_line}' failed to execute !")

    @lru_cache
    def access_grant(self) -> str:
        return self.translate(f"AskAI requires access to your files, folders and apps. Continue (yes/[no])?")

    @lru_cache
    def translate(self, text: str) -> str:
        """Translate text using the configured language."""
        return self._translator.translate(text)


assert AskAiMessages().INSTANCE is not None
