import os
from dataclasses import dataclass, field

from askai.core.enums.acc_color import AccColor
from askai.core.model.acc_response import AccResponse
from askai.core.model.action_plan import ActionPlan
from askai.core.model.model_result import ModelResult


@dataclass
class PipelineResponse:
    """TODO"""
    query: str
    answer: str | None = None
    accuracy: AccResponse | None = None


@dataclass
class SplitterResult:
    """TODO"""
    question: str
    responses: list[PipelineResponse] = field(default_factory=list)
    plan: ActionPlan | None = None
    model: ModelResult | None = None

    def final_response(self, acc_threshold: AccColor = AccColor.MODERATE) -> str:
        """TODO"""
        return os.linesep.join(
            list(map(lambda r: r.answer, filter(
                lambda acc: acc.accuracy and acc.accuracy.acc_color.passed(acc_threshold), self.responses)))
        )
