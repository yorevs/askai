import inspect
import re
from functools import lru_cache, cached_property
from textwrap import dedent
from typing import Optional

from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.metaclass.singleton import Singleton

from askai.core.askai_messages import msg
from askai.core.features.tools.analysis import check_output
from askai.core.features.tools.browser import browse
from askai.core.features.tools.general import display
from askai.core.features.tools.summarization import summarize
from askai.core.features.tools.terminal import execute_command, list_contents, open_command
from askai.exception.exceptions import ImpossibleQuery, TerminatingQuery


class Actions(metaclass=Singleton):
    """This class provides the AskAI available actions."""

    INSTANCE: 'Actions' = None

    RESERVED: list[str] = ['invoke', 'enlist']

    def __init__(self):
        self._all = dict(filter(
            lambda pair: pair[0] not in self.RESERVED and not pair[0].startswith('_'), {
                n: fn for n, fn in inspect.getmembers(self, predicate=inspect.ismethod)
            }.items()))

    @cached_property
    def tool_names(self) -> list[str]:
        return [str(dk) for dk in self._all.keys()]

    def invoke(self, tool: str, context: str = '') -> Optional[str]:
        """Invoke the tool with its arguments and context.
        :param tool: The tool to be performed.
        :param context: the tool context.
        """
        fn_name = None
        try:
            if tool_fn := re.findall(r'([a-zA-Z]\w+)\s*\((.*)\)', tool.strip()):
                fn_name = tool_fn[0][0].lower()
                fn = self._all[fn_name]
                args: list[str] = re.sub("['\"]", '', tool_fn[0][1]).split(',')
                args.append(context)
                return fn(*list(map(str.strip, args)))
        except KeyError as err:
            raise ImpossibleQuery(f"Tool not found: {fn_name} => {str(err)}")

        return None

    @lru_cache
    def enlist(self) -> str:
        """Return an 'os.linesep' separated string list of feature descriptions."""
        doc_strings: str = ''
        for fn in self._all.values():
            doc_strings += f"```{dedent(fn.__doc__)}```\n\n" if fn and fn.__doc__ else ''
        return doc_strings

    def _human_approval(self) -> bool:
        """Prompt for human approval. This is mostly used to execute terminal commands."""
        confirm_msg = (msg.access_grant())
        if (resp := line_input(confirm_msg).lower()) not in ("yes", "y"):
            raise ValueError(f"Terminal command execution was not approved '{resp}' !")
        self._approved = True

        return self._approved

    def browse(self, *args: str) -> str:
        """
        Tool: 'Internet Browsing Tool'
        Description: Use this tool to stay updated on the latest news and current events, particularly when you need real-time information quickly. This tool is ideal for acquiring fresh data but should not be used for queries about well-known facts.
        Usage: 'browse(search_query)'
          param `search_query`: The web search query in string format.
        """
        return browse(args[0])

    def check_output(self, *args: str) -> str:
        """
        Tool: 'Output Checker Tool'
        Description: Use this tool only after the output from a previous tool has been generated, to use that output as input for subsequent operations, thereby ensuring seamless workflow and enhanced efficiency.
        Usage: `check_output(question)`
          param `question`: The query from the user.
        """
        return check_output(args[0], args[1])

    def describe_image(self, *args: str) -> str:
        """
        Tool: 'Image Analysis Tool'
        Description: This tool is specifically designed for tasks that require the description or analysis of visual content in images.
        Usage: describe_image(image_path)
          param `image_path`: The file path of the image to be analyzed.
        """
        return str(NotImplementedError("Tool 'describe_image' is not yet implemented !"))

    def generate_content(self, *args: str) -> str:
        """
        Tool: 'Content Generation Tool'
        Description: This tool is specifically designed for tasks that require generating (creating) content such as, code, text, image, and others.
        Usage: generate_content(prompt, mime_type, path_name)
          param `prompt`: Specify the prompt to be used to generate the content.
          param `mime_type`: Specify the content type and format using MIME types.
          param `path_name`: Specify the directory path where you want to save the generated content. This parameter is optional and should be included only if you wish to save files directly to your disk. If not specified, the content will not be saved.
        """
        return str(NotImplementedError("Tool 'generate_content' is not yet implemented !"))

    def display(self, *args: str) -> str:
        """
        Tool: 'Display Tool'
        Description: Use this tool to display text. Join subsequent display usages together in only one call as you can input a list of texts do be displayed.
        Usage: 'display(text1, text2, ...)'
          param `texts`: The comma separated list of texts to be displayed.
        """
        return display(*args[:-1])

    def list_contents(self, *args: str) -> str:
        """
        Tool: 'List Tool'
        Description: This tool is designed for retrieving and displaying the contents of a specified folder. It is useful for quickly assessing the files and subdirectories within any directory.
        Usage: 'list_contents(folder)'
          param `folder`: A string representing the name of the directory whose contents you wish to list.
        """
        return list_contents(args[0])

    def open_command(self, *args: str) -> str:
        """
        Tool: 'Open Tool'
        Description: This tool is used to open or show the contents of files, folders, or applications on my system. This can be also used to play media files.
        Usage: 'open_command(pathname)'
          param `pathname`: The file, folder or application name.
        """
        return open_command(args[0])

    def summarize(self, *args: str) -> str:
        """
        Tool: 'Summarization Intent Tool'
        Description: Use this tool to display text. Consolidate subsequent display actions into a single call by inputting a list of texts.
        Usage: summarize(folder_name, glob)
          param `folder_name`: Name of the directory containing the files.
          param `glob`: Glob pattern to specify files within the folder for summarization.
        """
        return summarize(args[0], args[1])

    def terminal(self, *args: str) -> str:
        """
        Tool: 'Terminal Tool'
        Description: Use this tool to execute commands directly in the user terminal or process user-provided commands efficiently. Pay special attention to properly handling and escaping single or double quotes passed in the command parameters. Fix any syntax errors if you find any.
        Usage: 'terminal(shell_type, command)'
          param `shell_type`: A string that specifies the type of terminal environment (e.g., bash, zsh, powershell, etc).
          param `command`: The actual commands you wish to execute in the terminal.
        """
        # TODO Check for permission before executing
        return execute_command(args[0], args[1])

    def terminate(self, *args: str) -> None:
        """
        Tool: 'Terminating Intention Tool'
        Description: Use this tool when the user decides to conclude the interaction. This function ensures a smooth and clear ending to the session, confirming user intent to terminate the dialogue.
        Usage: 'terminate(reason)'
          param `reason`: A string indicating the reason for termination.
        """
        raise TerminatingQuery(args[0])


assert (features := Actions().INSTANCE) is not None
