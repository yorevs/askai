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

    @property
    def val(self) -> int:
        """Gets the integer value of the verbosity level.
        :return: The integer representation of the verbosity level.
        """
        return int(self.value)

    def match(self, level: "Verbosity") -> bool:
        """Checks if the current verbosity level is less than or equal to the given level.
        :param level: The verbosity level to compare against.
        :return: True if the current level is less than or equal to the given level, otherwise False.
        """
        return self.val <= level.val
