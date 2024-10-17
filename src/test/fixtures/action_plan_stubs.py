from askai.core.model.action_plan import ActionPlan
from askai.core.model.model_result import ModelResult
from hspylib.core.tools.dict_tools import get_or_default
from types import SimpleNamespace
from typing import Optional


def stub_response(index: int) -> Optional[ActionPlan]:
    # Fields: question, speak, primary_goal, sub_goals, tasks, model
    responses: list = [
        ActionPlan(
            "list my downloads",
            "I will help you list the contents of your 'Downloads' folder.",
            "List the contents of the 'Downloads' folder",
            False,
            [],
            [
                SimpleNamespace(
                    **{
                        "id": "1",
                        "task": "List the contents of the 'Downloads' folder",
                        "path": "/Users/hjunior/Downloads",
                    }
                )
            ],
            ModelResult.default(),
        ),
        ActionPlan(
            "hello",
            "Hello! How can I assist you today?",
            "Respond to the user's greeting.",
            True,
            [],
            [],
            ModelResult.default(),
        ),
        ActionPlan(
            "List my downloads and let me know if there is any image.",
            "I will list the contents of your downloads folder and check for any image files present.",
            "List the contents of the downloads folder and identify any image files",
            False,
            [
                SimpleNamespace(**{"id": "1", "sub_goal": "List the contents of the downloads folder"}),
                SimpleNamespace(**{"id": "2", "sub_goal": "Identify image files in the downloads folder"}),
            ],
            [
                SimpleNamespace(
                    **{
                        "id": "1",
                        "task": "List the contents of the downloads folder",
                        "path": "/Users/hjunior/Downloads",
                    }
                ),
                SimpleNamespace(
                    **{
                        "id": "2",
                        "task": "Identify image files in the downloads folder",
                        "path": "/Users/hjunior/Downloads",
                    }
                ),
            ],
            ModelResult.default(),
        ),
    ]

    return get_or_default(responses, index, None)
