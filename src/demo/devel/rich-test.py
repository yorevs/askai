#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from rich.console import Console
from rich.markdown import Markdown

console = Console(force_terminal=True, color_system="truecolor")

sample = """```python
def greet(name):
    print(f"Hello, {name}!")

greet("Hugs")
```"""

themes = ["ansi_dark", "ansi_light", "dracula", "monokai", "nord", "solarized-dark", "github"]

for theme in themes:
    console.rule(f"[bold cyan]{theme}")
    console.print(Markdown(sample, code_theme=theme))
