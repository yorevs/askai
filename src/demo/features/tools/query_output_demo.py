from pathlib import Path
from textwrap import dedent

from hspylib.core.enums.charset import Charset

from askai.core.features.tools.analysis import query_output
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text
from utils import init_context

BASE_DIR: Path = Path(__file__).parent

FILES_FN: str = 'ctx-files.txt'

REMINDERS_FN: str = 'ctx-reminders.txt'

CTX: str = Path(str(BASE_DIR) + '/samples/' + REMINDERS_FN).read_text(encoding=Charset.UTF_8.val)


if __name__ == '__main__':
    queries_files: list[str] = [
        "What should I do first ?",
        "What should I do after that ?",
        "What should I do after that ?",
        "What should I do after that ?",
        "What should I do last ?"
    ]
    queries_reminders: list[str] = [
        "Is there any reminder?",
        "Is there any image?",
        "Is there any music file?",
        "Is there any .zip file?",
        "Is there any whale?",
    ]
    init_context("query-output-demo")
    ctx: str = dedent(CTX)
    display_text(f"\n```bash\n{ctx}\n```\n")
    # Provide the context
    shared.context.push('HISTORY', ctx)
    for query in queries_files:
        print(f"({shared.context.size('HISTORY')}/{shared.context.max_context_size})", "QUESTION: ", query)
        resp: str = query_output(query)
        shared.context.push('HISTORY', query)
        shared.context.push('HISTORY', resp, 'assistant')
