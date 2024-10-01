from askai.core.enums.acc_color import AccColor
from askai.core.model.acc_response import AccResponse
from hspylib.core.tools.dict_tools import get_or_default
from typing import Optional


def stub_response(index: int) -> Optional[AccResponse]:
    # Fields: acc_color, accuracy, reasoning, tips
    responses: list = [
        AccResponse(
            AccColor.EXCELLENT,
            100.00,
            "The AI response is perfect in responding to the user's question, providing detailed and accurate information.",
            "The response can be improved by adding more personalized information or functionalities to enhance the user experience.",
        )
    ]

    return get_or_default(responses, index, None)
