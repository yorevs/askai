import atexit
import logging as log

from hspylib.core.tools.commons import log_init
from hspylib.core.tools.text_tools import ensure_endswith

from askai.core.askai_events import AskAiEvents
from askai.core.component.cache_service import cache
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text


def init_context(log_name: str, context_size: int = 1000) -> None:
    """TODO"""
    log_init(f"{ensure_endswith(log_name, '.log')}", level=log.INFO)
    cache.read_query_history()
    shared.create_engine(engine_name="openai", model_name="gpt-3.5-turbo")
    shared.create_context(context_size)
    AskAiEvents.ASKAI_BUS.events.reply.subscribe(cb_event_handler=lambda ev: display_text(ev.args.message))
    atexit.register(cache.save_query_history)
