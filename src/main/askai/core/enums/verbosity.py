from hspylib.core.enums.enumeration import Enumeration


class Verbosity(Enumeration):
    """Represents different verbosity levels for logging or output.
    Attributes:
        MINIMUM (int): The minimum verbosity level.
        LOW (int): A low verbosity level.
        NORMAL (int): The normal verbosity level.
        DETAILED (int): A detailed verbosity level.
        FULL (int): The full verbosity level.
    """

    # fmt: off
    MINIMUM     = 1
    LOW         = 2
    NORMAL      = 3
    DETAILED    = 4
    FULL        = 5
    # fmt: on

    def __eq__(self, other: "Verbosity") -> bool:
        return self.val == other.val

    def __lt__(self, other) -> bool:
        return self.val < other.val

    def __le__(self, other) -> bool:
        return self.val <= other.val

    def __gt__(self, other) -> bool:
        return self.val > other.val

    def __ge__(self, other) -> bool:
        return self.val >= other.val

    @property
    def val(self) -> int:
        """Gets the integer value of the verbosity level.
        :return: The integer representation of the verbosity level.
        """
        return int(self.value)
