from askai.__classpath__ import classpath
from askai.core.askai_events import events
from askai.core.commander.commander import commands
from askai.core.component.cache_service import cache
from askai.core.enums.router_mode import RouterMode
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text
from clitt.core.tui.line_input.keyboard_input import KeyboardInput
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import log_init
from hspylib.core.tools.text_tools import ensure_endswith
from pathlib import Path
from typing import Literal

import atexit
import logging as log
import os

BASE_DIR: str = str(classpath.resource_path).replace("/main/askai/", "/demo/")

RESOURCES: dict[str, any] = {"files": "ctx-files.txt", "reminders": "ctx-reminders.txt", "songs": "ctx-songs.txt"}


def init_context(
    log_name: str | None = None,
    log_level: int = log.NOTSET,
    rich_logging: bool = False,
    console_enable: bool = False,
    context_size: int = 1000,
    engine_name: Literal["openai"] = "openai",
    model_name: Literal["gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-4o-mini"] = "gpt-4o-mini",
) -> None:
    """Initialize AskAI context and startup components."""
    if log_name:
        log_dir: str = os.environ.get("HHS_LOG_DIR", os.getcwd())
        log_init(
            filename=f"{os.path.join(log_dir, ensure_endswith(log_name, '.log'))}",
            level=log_level,
            rich_logging=rich_logging,
            console_enable=console_enable,
        )
    KeyboardInput.preload_history(cache.load_input_history(commands()))
    shared.create_engine(engine_name=engine_name, model_name=model_name, mode=RouterMode.default())
    shared.create_context(context_size)
    events.reply.subscribe(cb_event_handler=lambda ev: display_text(ev.args.reply))
    atexit.register(cache.save_input_history)


def get_resource(resource_path: str) -> str:
    return Path(f"{BASE_DIR}/{RESOURCES[resource_path]}").read_text(encoding=Charset.UTF_8.val)
