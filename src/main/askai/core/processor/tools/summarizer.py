from textwrap import dedent

from langchain_core.tools import tool


@tool
def summarize(paths) -> str:
    """Summarize files and folders."""
    print(f"Summarizing: '{','.join(paths)}'")
    return dedent("""You have 2 tasks to do:
    1. Got to the dentist
    2. Create a project X report.
    """)
