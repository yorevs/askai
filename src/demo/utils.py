import atexit
import logging as log
from pathlib import Path
from typing import Literal

from clitt.core.tui.line_input.keyboard_input import KeyboardInput
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import log_init
from hspylib.core.tools.text_tools import ensure_endswith

from askai.__classpath__ import classpath
from askai.core.askai_events import events
from askai.core.commander.commander import commands
from askai.core.component.cache_service import cache
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text

BASE_DIR: str = str(classpath.resource_path()).replace("/main/askai/", "/demo/")

RESOURCES: dict[str, any] = {"files": "ctx-files.txt", "reminders": "ctx-reminders.txt", "songs": "ctx-songs.txt"}


def init_context(
    log_name: str,
    context_size: int = 1000,
    log_level: int = log.INFO,
    engine_name: Literal["openai"] = "openai",
    model_name: Literal["gpt-3.5-turbo", "gpt-4", "gpt-4o"] = "gpt-3.5-turbo",
) -> None:
    """Initialize AskAI context and startup components."""
    log_init(f"{ensure_endswith(log_name, '.log')}", level=log_level)
    KeyboardInput.preload_history(cache.load_history(commands()))
    shared.create_engine(engine_name=engine_name, model_name=model_name)
    shared.create_context(context_size)
    events.reply.subscribe(cb_event_handler=lambda ev: display_text(ev.args.message))
    atexit.register(cache.save_query_history)


def get_resource(resource_path: str) -> str:
    return Path(f"{BASE_DIR}/{RESOURCES[resource_path]}").read_text(encoding=Charset.UTF_8.val)
