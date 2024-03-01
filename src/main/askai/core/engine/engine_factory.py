from typing import List

from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_not_none

from askai.core.engine.ai_engine import AIEngine
from askai.core.engine.openai.openai_engine import OpenAIEngine
from askai.core.engine.openai.openai_model import OpenAIModel
from askai.exception.exceptions import NoSuchEngineError


class EngineFactory(metaclass=Singleton):
    """TODO"""

    INSTANCE: 'EngineFactory' = None

    _ACTIVE_AI_ENGINE: AIEngine = None

    @classmethod
    def create_engine(cls, engine_name: str | List[str], engine_model: str | List[str]) -> AIEngine:
        """Find the suitable AI engine according to the provided engine name.
        :param engine_name: the AI engine name.
        :param engine_model: the AI engine model.
        """
        engine = engine_name.lower() if isinstance(engine_name, str) else engine_name[0].lower()
        model = engine_model.lower() if isinstance(engine_model, str) else engine_model[0].lower()
        match engine:
            case "openai":
                cls._ACTIVE_AI_ENGINE = OpenAIEngine(OpenAIModel.of_name(model) or OpenAIModel.GPT_3_5_TURBO)
            case "palm":
                raise NoSuchEngineError("Google 'paml' is not yet implemented!")
            case _:
                raise NoSuchEngineError(f"Engine name: {engine_name}  model: {engine_model}")

        return cls._ACTIVE_AI_ENGINE

    @classmethod
    def active_ai(cls) -> AIEngine:
        return check_not_none(cls._ACTIVE_AI_ENGINE, "No AI engine has been created yet!")


assert EngineFactory().INSTANCE is not None
