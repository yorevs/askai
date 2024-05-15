from askai.core.features.router import router
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text
from utils import init_context


if __name__ == '__main__':
    queries: list[str] = [
        "List my downloads and let me know if there is any reminder.",
        "Open 1",
        "Based on that reminder, what should I do first?",
        "What should I do next?",
        "What should I do next?",
        "What should I do next?",
        "What should I do last?",
    ]
    init_context('router-demo')
    for query in queries:
        print(f"({shared.context.size('HISTORY')}/{shared.context.max_context_size})", "QUESTION: ", query)
        resp: str = router.process(query)
        display_text(resp)
