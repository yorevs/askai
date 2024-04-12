import inspect
import re
from functools import lru_cache
from textwrap import dedent
from typing import Optional

from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.metaclass.singleton import Singleton

from askai.core.askai_messages import msg
from askai.core.features.tools.analysis import check_output
from askai.core.features.tools.browser import browse
from askai.core.features.tools.general import fetch, display
from askai.core.features.tools.summarization import summarize
from askai.core.features.tools.terminal import execute_command, list_contents, open_command
from askai.exception.exceptions import ImpossibleQuery, UnintelligibleQuery, TerminatingQuery


class Actions(metaclass=Singleton):
    """This class provides the AskAI available actions."""

    INSTANCE: 'Actions' = None

    RESERVED: list[str] = ['invoke', 'enlist']

    def __init__(self):
        self._all = dict(filter(
            lambda pair: pair[0] not in self.RESERVED and not pair[0].startswith('_'), {
                n: fn for n, fn in inspect.getmembers(self, predicate=inspect.ismethod)
            }.items()))

    def invoke(self, action: str, context: str = '') -> Optional[str]:
        """Invoke the action with its arguments and context.
        :param action: The action to be performed.
        :param context: the action context.
        """
        re_fn = r'([a-zA-Z]\w+)\s*\((.*)\)'
        fn_name = None
        try:
            if act_fn := re.findall(re_fn, action):
                fn_name = act_fn[0][0].lower()
                fn = self._all[fn_name]
                args: list[str] = re.sub("['\"]", '', act_fn[0][1]).split(',')
                args.append(context)
                return fn(*list(map(str.strip, args)))
        except KeyError as err:
            raise ImpossibleQuery(f"Command not found: {fn_name} => {str(err)}")

        return None

    @lru_cache
    def enlist(self) -> str:
        """Return an 'os.linesep' separated string list of feature descriptions."""
        doc_strings: str = ''
        for fn in self._all.values():
            doc_strings += f"{dedent(fn.__doc__)}\n{'-' * 18}\n" if fn and fn.__doc__ else ''
        return doc_strings

    def _human_approval(self) -> bool:
        """Prompt for human approval. This is mostly used to execute terminal commands."""
        confirm_msg = (msg.access_grant())
        if (resp := line_input(confirm_msg).lower()) not in ("yes", "y"):
            raise ValueError(f"Terminal command execution was not approved '{resp}' !")
        self._approved = True

        return self._approved

    def unintelligible(self, *args: str) -> None:
        """
        Feature: 'Unintelligible Question Handler'
        Description: Implement this feature when a user's question is unclear or difficult to comprehend.
        Usage: 'unintelligible(question, reason)'
          - `question` The question posed by the user that is considered unintelligible.
          - `reason` Explanation of why the question is deemed unintelligible.
        """
        raise UnintelligibleQuery(f"{args[1]}: '{args[0]}'")

    def terminate(self, *args: str) -> None:
        """
        Feature: 'Terminating Intention Handler'
        Description: Employ this feature when the user decides to conclude the interaction. This function ensures a
        smooth and clear ending to the session, confirming user intent to terminate the dialogue.
        Usage: 'terminate()'.
        """
        raise TerminatingQuery('')

    def impossible(self, *args: str) -> None:
        """
        Feature: 'Impossible Action or Plan'
        Description: This feature should be used when an action or plan is unfeasible or cannot be executed.
        Usage: 'impossible(reason)'.
          - `reason` A description of why the action or plan is impossible to implement.
        """
        raise ImpossibleQuery(' '.join(args))

    def terminal(self, *args: str) -> str:
        """
        Feature: 'Execute Terminal Commands'
        Description: Utilize this feature to run commands directly in various terminal environments. This feature is particularly useful when other specific tools or features do not meet your requirements. Use this feature also when you haven't found any other feature that matches the desired action from the user.
        Usage: 'terminal(term_type, command)'
          - `term_type` A string that specifies the type of terminal environment (e.g., bash, zsh, powershell, etc.).
          - `command` The actual commands you wish to execute in the terminal.
        Example: To find all mp3 files in a directory using bash, use: `terminal('bash', 'find . -maxdepth 1 -name "*.mp3")`
        """
        # TODO Check for permission before executing
        return execute_command(args[0], args[1])

    def list_contents(self, *args: str) -> str:
        """
        Feature: 'List Folder Contents'
        Description: This feature is designed for retrieving and displaying the contents of a specified folder. It is useful for quickly assessing the files and subdirectories within any directory.
        Usage: 'list_contents(folder)'
          - `folder`: A string representing the name of the directory whose contents you wish to list.
        Example: To list the contents of the HomeSetup docs folder, use: `list_contents('~/HomeSetup/docs')`.
        """
        return list_contents(args[0])

    def open_command(self, *args: str) -> str:
        """
        Feature: 'Open files, folders, and applications'
        Description: This feature is used to open any file, folder, or application on your system.
        Usage: 'open_command(pathname)'
          - `pathname` The file, folder or application name.
        Example: To open the song file 'the-trooper.mp3', use: `open_command('the-trooper.mp3')`
        """
        return open_command(args[0])

    def check_output(self, *args: str) -> str:
        """
        Feature: 'Check Output'
        Description: This function should be used after executing a command that generates an output. It is useful for
        situations where the output of one function is needed as input in subsequent calls.
        Usage: `check_output(question)`
          - `question`: The query from the user.
        Example:
          - User: 'list my downloads and tell me if there is any image'.
          - Assistant:
            1. list_contents('~Downloads').
            2. check_output('Is there any image on the list').
        """
        return check_output(args[0], args[1])

    def fetch(self, *args: str) -> str:
        """
        Feature: 'Time-independent Database Retrieval'
        Description: This feature facilitates the retrieval of database information independently of time constraints,
        enhancing consistency and reliability in data analysis. It proves particularly beneficial in applications that
        demand persistent data accuracy, such as report generation and historical data review. This functionality is
        also invaluable for resolving ambiguities in data interpretation, ensuring clarity and precision in outputs.
        Usage: `fetch(question)`
          - `question`: Specify the query or prompt for data retrieval in a consistent and time-independent manner.
        Example:
          - To retrieve the size of the moon: `fetch("Retrieve the size of the moon")`
        """
        return fetch(args[0])

    def browse(self, *args: str) -> str:
        """
        Feature: 'Internet Browsing'
        Description: Utilize this feature to obtain information on current events or recent developments. It's
        particularly useful for up-to-date news inquiries or when fresh data is needed quickly.
        Usage: 'browse(search_query)'
          - `search_query`: The web search query in string format.
        Example:
          - To find the latest news on climate change, you would use: browse("latest news on climate change")
        """
        return browse(args[0])

    def display(self, *args: str) -> str:
        """
        Feature: 'display'
        Description: Use this function to display plain text. It is designed solely for display purposes and not for fetching or processing data.
        Usage: 'display(text, ...)'
          - `text`: The comma separated list of texts to be displayed.
        """
        return display(*args[:-1])

    def summarize_files(self, *args: str) -> str:
        """
        Feature: 'Summarization of Files and Folders'
        Description: This feature is designed to efficiently summarize the contents of files and folders. It should be
        activated specifically when requests for summarizations or analogous operations are explicitly made.
        Usage: summarize_files(folder_name, path_wildcard)
          - `folder_name`: Name of the directory containing the files.
          - `path_wildcard`: Glob pattern to specify files within the folder for summarization.
        """
        return summarize(args[0], args[1])

    def describe_image(self, *args: str) -> str:
        """
        Feature: 'Image Analysis'
        Description: This feature is applicable when there is a need to describe or analyze an image.
        Usage: describe_image(image_path)
          - `image_path`: The file path of the image to be analyzed.
        Example:
          - To analyze an image located at 'path/to/image.jpg', use: describe_image('path/to/image.jpg').
        """
        return str(NotImplementedError("Feature 'describe_image' is not yet implemented !"))


assert (features := Actions().INSTANCE) is not None
