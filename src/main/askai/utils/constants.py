from hspylib.modules.cli.keyboard import Keyboard


class Constants:
    """Provide as class contains all AskAi constants."""

    # Interactive mode termination expressions.
    TERM_EXPRESSIONS = r"^((good)?(bye ?)+|(tchau ?)+|(ciao ?)|quit|exit|[tT]hank(s| you)).*"

    # Push to talk string value.
    PUSH_TO_TALK = Keyboard.VK_CTRL_L

    DISPLAY_BUS = "display-bus"

    CAPTURER_BUS = "capturer-bus"

    DISPLAY_EVENT = "display-event"

    STREAM_EVENT = "stream-event"

    TERM_EVENT = "terminate-event"

    STDOUT_CAPTURED = "stdout-captured"

    STDERR_CAPTURED = "stderr-captured"


