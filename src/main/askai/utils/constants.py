from hspylib.core.enums.charset import Charset
from hspylib.modules.cli.keyboard import Keyboard


class Constants:
    """Provide as class contains all AskAi constants."""

    # Interative mode termination expressions.
    TERM_EXPRESSIONS = r"^((good)?(bye ?)+|(tchau ?)+|(ciao ?)|quit|exit|[tT]hank(s| you)).*"

    # Default application language.
    DEFAULT_LANGUAGE = "en_US"

    # Default application text encoding.
    DEFAULT_ENCODING = Charset.UTF_8.val

    # Push to talk string value.
    PUSH_TO_TALK = Keyboard.VK_CTRL_L
