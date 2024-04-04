from hspylib.core.enums.enumeration import Enumeration


class RagResponse(Enumeration):
    """TODO"""

    # fmt: off

    GOOD        = 'Green'

    MODERATE    = 'Yellow'

    BAD         = 'Red'

    # fmt: on

    @property
    def is_bad(self) -> bool:
        return self == self.BAD

    @property
    def is_moderate(self) -> bool:
        return self == self.MODERATE

    @property
    def is_good(self) -> bool:
        return self == self.GOOD
