#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine
      @file: engine_factory.py
   @created: Tue, 23 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from askai.core.engine.ai_engine import AIEngine
from askai.core.engine.ai_model import AIModel
from askai.core.engine.openai.openai_engine import OpenAIEngine
from askai.core.engine.openai.openai_model import OpenAIModel
from askai.exception.exceptions import NoSuchEngineError
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_not_none
from typing import List


class EngineFactory(metaclass=Singleton):
    """TODO"""

    INSTANCE: "EngineFactory"

    _ACTIVE_AI_ENGINE: AIEngine | None = None

    @classmethod
    def create_engine(cls, engine_name: str | List[str], engine_model: str | List[str]) -> AIEngine:
        """Find the suitable AI engine according to the provided engine name.
        :param engine_name: the AI engine name.
        :param engine_model: the AI engine model.
        """
        engine_name = engine_name[0] if isinstance(engine_name, list) else engine_name
        model_name = engine_model[0] if isinstance(engine_model, list) else engine_model
        match engine_name:
            case "openai":
                model: AIModel = OpenAIModel.of_name(model_name) if model_name else None
                cls._ACTIVE_AI_ENGINE = OpenAIEngine(model or OpenAIModel.GPT_4_O_MINI)
            case "gemini":
                raise NoSuchEngineError("Google 'paml' is not yet implemented!")
            case _:
                raise NoSuchEngineError(f"Engine name: {engine_name}  model: {engine_model}")

        return cls._ACTIVE_AI_ENGINE

    @classmethod
    def active_ai(cls) -> AIEngine:
        return check_not_none(cls._ACTIVE_AI_ENGINE, "No AI engine has been created yet!")


assert EngineFactory().INSTANCE is not None
