from askai.core.router.tools.analysis import query_output
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text
from utils import get_resource, init_context

if __name__ == "__main__":
    queries_reminders: list[str] = [
        "What should I do first ?",
        "What should I do after that ?",
        "What should I do after that ?",
        "What should I do after that ?",
        "What should I do last ?",
    ]
    queries_files: list[str] = [
        "Is there any reminder?",
        "Is there any image?",
        "Is there any music file?",
        "Is there any .zip file?",
        "Is there any whale?",
    ]
    init_context("query-output-demo")
    ctx: str = get_resource("reminders")
    display_text(f"\n```bash\n{ctx}\n```\n")
    # Provide the context
    shared.context.push("HISTORY", ctx)
    for query in queries_reminders:
        print(f"({shared.context.size('HISTORY')}/{shared.context.max_context_size})", "QUESTION: ", query)
        resp: str = query_output(query)
        shared.context.push("HISTORY", query)
        shared.context.push("HISTORY", resp, "assistant")
