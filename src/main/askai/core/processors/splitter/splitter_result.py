from askai.core.enums.acc_color import AccColor
from askai.core.model.acc_response import AccResponse
from askai.core.model.action_plan import ActionPlan
from askai.core.model.model_result import ModelResult
from dataclasses import dataclass, field

import os


@dataclass
class PipelineResponse:
    """Represent a pipeline response for the given query."""

    query: str
    answer: str | None = None
    accuracy: AccResponse | None = None


@dataclass
class SplitterResult:
    """Represent the result of the splitting user request"""

    question: str
    responses: list[PipelineResponse] = field(default_factory=list)
    plan: ActionPlan | None = None
    model: ModelResult | None = None

    def final_response(self, acc_threshold: AccColor = AccColor.MODERATE) -> str:
        """Return the final response to the user."""
        return os.linesep.join(
            list(
                map(
                    lambda r: r.answer,
                    filter(lambda acc: acc.accuracy and acc.accuracy.acc_color.passed(acc_threshold), self.responses),
                )
            )
        )
