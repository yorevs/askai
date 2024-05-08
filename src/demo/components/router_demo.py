from hspylib.core.tools.commons import log_init
import logging as log

from askai.core.component.cache_service import cache
from askai.core.features.router import router
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text

if __name__ == '__main__':
    log_init("router-demo.log", level=log.INFO)
    cache.read_query_history()
    shared.create_engine(engine_name="openai", model_name="gpt-3.5-turbo")
    shared.create_context(1000)

    q = "List my downloads and let me know if there is any reminder."
    print("QUESTION: ", q)
    display_text(router.process(q))

    q = "Open 1"
    print("QUESTION: ", q)
    display_text(router.process(q))

    q = "What should I do first?"
    print("QUESTION: ", q)
    display_text(router.process(q))

    q = "What should I do second?"
    print("QUESTION: ", q)
    display_text(router.process(q))

    q = "What should I do last?"
    print("QUESTION: ", q)
    display_text(router.process(q))
