from askai.core.features.rag.rag import resolve_x_refs
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text
from utils import init_context, get_resource

if __name__ == '__main__':
    queries_files: list[str] = [
        "Open 1",
        "Open second",
        "Open 3",
        "Open <AC/DC_Song>",
        "Open it",
        "Open any",
        "Open the most recent",
        "Open the most oldest",
        "open metalica"
    ]
    init_context('x_refs_demo')
    ctx: str = get_resource("songs")
    display_text(f"\n```bash\n{ctx}\n```\n")
    # Provide the context
    shared.context.push('HISTORY', ctx)
    shared.context.push('HISTORY', 'Is there any song about cars?')
    shared.context.push('HISTORY', 'Yes, there is. The song is "Highway to Hell"', 'assistant')
    for query in queries_files:
        print(f"({shared.context.size('HISTORY')}/{shared.context.max_context_size})", "QUESTION: ", query)
        resp: str = resolve_x_refs(query)
        display_text(f"Response: {resp}")
