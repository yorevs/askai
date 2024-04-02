import inspect
import re
from textwrap import dedent
from typing import Optional, Callable

from hspylib.core.metaclass.singleton import Singleton

from askai.core.askai_events import AskAiEvents
from askai.core.processor.tools.analysis import check_output
from askai.core.processor.tools.terminal import execute_command, list_contents


class Features(metaclass=Singleton):
    """TODO"""

    INSTANCE: 'Features' = None

    FEATURES: list[Callable] = None

    def __init__(self):
        self._all = dict(filter(
            lambda pair: pair[0] not in ['invoke', 'list_features'] and not pair[0].startswith('__'), {
                n: fn for n, fn in inspect.getmembers(self, predicate=inspect.ismethod)
            }.items()))

    def invoke(self, action: str, context: str = '') -> Optional[str]:
        """TODO"""
        re_fn = r'([a-zA-Z]\w+)\s*\((.*)\)'
        if act_fn := re.findall(re_fn, action):
            fn = self._all[act_fn[0][0]]
            args: list[str] = re.sub("['\"]", '', act_fn[0][1]).split(',')
            args.append(context)
            return fn(*list(map(str.strip, args)))
        return None

    def enlist(self) -> str:
        return dedent("""
        - "Internet browsing" -> Command = browse(query)
        - "List folder contents" -> Command = list_contents(folder)
        - "Terminal command execution" -> Command = terminal(shell, command)
        - "Summarization of files and folders" -> Command = summarize_files(glob)
        - "Check output" -> Command = check_output(question)
        - "Image analysis" -> Command = describe_image(image_path)
        - "Fetch from AI database" -> Command = fetch(query)
        - "Intelligible question" -> Command = intelligible(question)
        - "Terminate intent" -> Command = terminate(reason)
        - "Display text" -> Command = display(text)
        """)

    def browse(self, query: str) -> str:
        """Internet browsing.
        :param query: the query string.
        """
        pass

    def list_contents(self, *args: str) -> str:
        """List folder contents.
        """
        return list_contents(args[0])

    def terminal(self, *args: str) -> str:
        """Terminal command execution.
        """
        return execute_command(args[0], args[1])

    def summarize_files(self, glob: str) -> str:
        """Summarization of files and folders.
        """
        pass

    def check_output(self, *args: str) -> str:
        """Check output.
        :param output: The output to analyze.
        """
        return check_output(args[0], args[1])

    def describe_image(self, image_path: str) -> str:
        """Check output.
        :param image_path: The image file path.
        """
        pass

    def fetch(self, query: str) -> str:
        """Fetch from AI database.
        :param query
        """
        pass

    def intelligible(self, question: str) -> str:
        """Intelligible question.
        :param question: The intelligible question.
        """
        pass

    def terminate(self, reason: str) -> str:
        """Terminate intent.
        :param reason: The reason to terminate.
        """
        pass

    def display(self, text: str) -> None:
        """Display text.
        :param text: the text to be displayed.
        """
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=text)


assert (features := Features().INSTANCE) is not None

if __name__ == '__main__':
    print(features.invoke("terminal('bash', 'ls -lht ~/Downloads')"))
    features.display("Hugo Saporetti Junior")
