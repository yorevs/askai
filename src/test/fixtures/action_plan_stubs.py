from types import SimpleNamespace
from typing import Optional

from askai.core.model.action_plan import ActionPlan
from askai.core.model.model_result import ModelResult
from hspylib.core.tools.dict_tools import get_or_default


def stub_response(index: int) -> Optional[ActionPlan]:
    # Fields: question, speak, primary_goal, sub_goals, tasks, model
    responses: list = [
        ActionPlan(
            "list my downloads",
            "I will help you list the contents of your 'Downloads' folder.",
            "List the contents of the 'Downloads' folder",
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
            "I will greet the user and initiate the conversation.",
            "Respond to the user's greeting.",
            [],
            [SimpleNamespace(**{"id": "1", "task": "Direct: 'Hello! How can I assist you today?'"})],
            ModelResult.default(),
        ),
        ActionPlan(
            "List my downloads and let me know if there is any image.",
            "I will list the contents of your downloads folder and check for any image files present.",
            "List the contents of the downloads folder and identify any image files",
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
