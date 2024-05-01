import logging as log
import os
import re
import uuid
from functools import partial
from pathlib import Path

import nltk
from cachetools import LRUCache
from click import UsageError
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import is_debugging
from hspylib.core.tools.text_tools import ensure_endswith, elide_text
from hspylib.modules.application.version import Version
from hspylib.modules.eventbus.event import Event
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.suggester import SuggestFromList
from textual.widgets import MarkdownViewer, Input, Footer

from askai.__classpath__ import classpath
from askai.core.askai_configs import configs
from askai.core.askai_events import AskAiEvents, ASKAI_BUS_NAME, REPLY_EVENT, REPLY_ERROR_EVENT
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.commander.commander import askai
from askai.core.component.audio_player import player
from askai.core.component.cache_service import CACHE_DIR, cache
from askai.core.component.recorder import recorder
from askai.core.component.scheduler import scheduler
from askai.core.engine.ai_engine import AIEngine
from askai.core.features.router import router
from askai.core.support.chat_context import ChatContext
from askai.core.support.shared_instances import shared
from askai.core.tui.app_widgets import Splash, AppInfo
from askai.core.tui.header import Header
from askai.exception.exceptions import ImpossibleQuery, MaxInteractionsReached, InaccurateResponse, TerminatingQuery

SOURCE_DIR: Path = classpath.source_path()

RESOURCE_DIR: Path = classpath.resource_path()


class AskAiApp(App):
    """The AskAI Textual application."""

    CSS_PATH = f"{RESOURCE_DIR}/askai.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear", "Clear Console"),
    ]

    SPLASH_IMAGE: str = classpath.get_resource("splash.txt").read_text(encoding=Charset.UTF_8.val)

    RE_ASKAI_CMD: str = r'^(?<!\\)/(\w+)( (.*))*$'

    def __init__(
        self,
        quiet: bool,
        debug: bool,
        tempo: int,
        engine_name: str,
        model_name: str,
    ):
        super().__init__()
        self._session_id = str(uuid.uuid4()).replace('-', '')[:8]
        self._input_history = ['/help', '/settings', '/voices', '/debug']
        self._question: str | None = None
        self._engine: AIEngine = shared.create_engine(engine_name, model_name)
        self._context: ChatContext = shared.create_context(self._engine.ai_token_limit())
        # Setting configs from program args.
        configs.is_speak = not quiet
        configs.is_debug = is_debugging() or debug
        configs.tempo = tempo
        self._console_path = Path(f"{CACHE_DIR}/askai-{self.session_id}.md")
        if not self._console_path.exists():
            self._console_path.touch()

    def __str__(self) -> str:
        device_info = f"{recorder.input_device[1]}" if recorder.input_device else ""
        device_info += f", AUTO-SWAP {'ON' if recorder.is_auto_swap else 'OFF'}"
        speak_info = str(configs.tempo) + ' @' + shared.engine.configs.tts_voice
        cur_dir = elide_text(str(Path(os.curdir).absolute()), 67, "…")
        return (
            f"     Engine: {self.engine} \n"
            f"   Language: {configs.language} \n"
            f"    WorkDir: {cur_dir} \n\n"
            f" Microphone: {device_info or 'Undetected'} \n"
            f"  Debugging: {'ON' if self.is_debugging else 'OFF'} \n"
            f"   Speaking: {'ON, tempo: ' + speak_info if self.is_speak else 'OFF'} \n"
            f"    Caching: {'ON, TTL: ' + str(configs.ttl) if cache.is_cache_enabled() else 'OFF'} \n"
        )

    @property
    def engine(self) -> AIEngine:
        return self._engine

    @property
    def context(self) -> ChatContext:
        return self._context

    @property
    def cache_enabled(self) -> bool:
        return configs.is_cache

    @property
    def question(self) -> str:
        return self._question

    @property
    def is_debugging(self) -> bool:
        return configs.is_debug

    @property
    def is_speak(self) -> bool:
        return configs.is_speak

    @property
    def nickname(self) -> str:
        return f"*  Taius*"

    @property
    def username(self) -> str:
        return f"**  {prompt.user.title()}**"

    @property
    def md_console(self) -> MarkdownViewer:
        """Get the MarkdownViewer widget."""
        return self.query_one(MarkdownViewer)

    @property
    def info(self) -> AppInfo:
        """Get the AppInfo widget."""
        return self.query_one(AppInfo)

    @property
    def splash(self) -> Splash:
        """Get the Splash widget."""
        return self.query_one(Splash)

    @property
    def line_input(self) -> Input:
        """Get the Input widget."""
        return self.query_one(Input)

    @property
    def header(self) -> Header:
        """Get the Input widget."""
        return self.query_one(Header)

    @property
    def footer(self) -> Footer:
        """Get the Input widget."""
        return self.query_one(Footer)

    @property
    def session_id(self) -> str:
        """Get the Session id."""
        return self._session_id

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        suggester = SuggestFromList(self._input_history, case_sensitive=False)
        suggester.cache = LRUCache(1024)
        yield Header(id="header")
        with ScrollableContainer(id="container"):
            yield AppInfo("")
            yield Splash(self.SPLASH_IMAGE)
            yield MarkdownViewer()
        yield Input(
            id="input",
            placeholder=f"Message {self.engine.nickname()}",
            suggester=suggester
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Called application is mounted."""
        self.screen.title = f"AskAI v{Version.load(load_dir=classpath.source_path())}"
        self.screen.sub_title = self.engine.ai_model_name()
        self.header.disabled = True
        self.line_input.disabled = True
        self.footer.disabled = True
        self.md_console.set_class(True, "-hidden")
        self._startup()

    async def activate_markdown(self) -> None:
        """Activate the Markdown console."""
        self.md_console.set_classes("-visible")
        self.md_console.focus()
        self.md_console.show_table_of_contents = True
        await self.md_console.go(self._console_path)

    async def action_clear(self) -> None:
        """Clear the output console."""
        open(self._console_path, 'w', encoding=Charset.UTF_8.val).close()
        await self.md_console.go(self._console_path)

    @work
    async def display_text(self, markdown_text: str) -> None:
        """Send the text to the Markdown console."""
        with open(self._console_path, 'a', encoding=Charset.UTF_8.val) as f_console:
            f_console.write(f"{ensure_endswith(markdown_text, os.linesep * 2)}")
            f_console.flush()
        await self.md_console.go(self._console_path)

    @on(Input.Submitted)
    async def on_submit(self, submitted: Input.Submitted) -> None:
        """A coroutine to handle a input submission."""
        question: str = submitted.value
        self.line_input.clear()
        self.line_input.loading = True
        self.display_text(f"{self.username}: {question}")
        self._ask_and_reply(question)

    async def reply(self, message: str) -> None:
        """Reply to the user with the AI response.
        :param message: The message to reply to the user.
        """
        if self.is_speak:
            self.engine.text_to_speech(message, f"{self.nickname}: ")
        else:
            self.display_text(f"{self.nickname}: {message}")

    async def reply_error(self, message: str) -> None:
        """Reply API or system errors.
        :param message: The error message to be displayed.
        """
        log.error(message)
        if self.is_speak:
            self.engine.text_to_speech(f"Error: {message}", f"{self.nickname}: ")
        else:
            self.display_text(f"{self.nickname}: Error: {message}")

    @work(thread=True)
    async def _ask_and_reply(self, question: str) -> bool:
        """Ask the question and provide the reply.
        :param question: The question to ask to the AI engine.
        """
        status = True
        try:
            if command := re.search(self.RE_ASKAI_CMD, question):
                args: list[str] = list(filter(
                    lambda a: a and a != 'None', re.split(r'\s', f"{command.group(1)} {command.group(2)}")
                ))
                askai(args, standalone_mode=False)
            elif not (reply := cache.read_reply(question)):
                log.debug('Response not found for "%s" in cache. Querying from %s.', question, self.engine.nickname())
                await self.reply(message=msg.wait())
                if output := router.process(question):
                    await self.reply(output)
            else:
                log.debug("Reply found for '%s' in cache.", question)
                await self.reply(reply)
        except (NotImplementedError, ImpossibleQuery) as err:
            await self.reply_error(str(err))
        except (MaxInteractionsReached, InaccurateResponse, ValueError) as err:
            await self.reply_error(msg.unprocessable(type(err)))
        except UsageError as err:
            await self.reply_error(msg.invalid_command(err))
        except TerminatingQuery:
            status = False

        self.line_input.loading = False

        return status

    @work(thread=True)
    async def _startup(self) -> None:
        """Initialize the application."""
        self.header.disabled = False
        self.line_input.disabled = False
        self.footer.disabled = False
        askai_bus = AskAiEvents.get_bus(ASKAI_BUS_NAME)
        askai_bus.subscribe(REPLY_EVENT, self._cb_reply_event)
        askai_bus.subscribe(REPLY_ERROR_EVENT, partial(self._cb_reply_event, error=True))
        nltk.download("averaged_perceptron_tagger", quiet=True, download_dir=CACHE_DIR)
        cache.set_cache_enable(self.cache_enabled)
        cache.read_query_history()
        player.start_delay()
        scheduler.start()
        recorder.setup()
        self.info.info_text = str(self)
        await self.activate_markdown()
        # At this point the application is ready.
        log.info("AskAI is ready to use!")
        self.splash.set_class(True, "-hidden")
        self.line_input.focus()
        await self.reply(msg.welcome(prompt.user.title()))

    def _cb_reply_event(self, ev: Event, error: bool = False) -> None:
        """Callback to handle reply events.
        :param ev: The reply event.
        :param error: Whether the event is an error not not.
        """
        if error:
            self.reply_error(ev.args.message)
        else:
            verbose = ev.args.verbosity.lower()
            if verbose == "normal" or self.is_debugging:
                if ev.args.erase_last:
                    pass
                self.reply(ev.args.message)


if __name__ == "__main__":
    app = AskAiApp(True, False, 1, 'openai', 'gpt-3.5-turbo')
    app.run()
