from hspylib.core.enums.enumeration import Enumeration

import re


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

    @classmethod
    def matches(cls, output: str) -> re.Match:
        return re.search(cls._re(), output.replace('\n', ' '), re.IGNORECASE)

    @classmethod
    def _re(cls) -> str:
        return rf"(^{'|'.join(cls.values())})[:,-]\s*(.+)"

    @classmethod
    def strip_code(cls, message: str) -> str:
        """Strip the color code from the message"""
        mat = cls.matches(message)
        return str(mat.group(2)).strip() if mat else message

    @classmethod
    def of_status(cls, status: str) -> "RagResponse":
        return cls.of_value(status.title())


if __name__ == "__main__":
    print(RagResponse.values())
    print(RagResponse.strip_code("Red, Because I said so"))
