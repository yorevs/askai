#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.router.model_selector
      @file: model_selector.py
   @created: Tue, 24 Jun 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_prompt import prompt
from askai.core.component.geo_location import geo_location
from askai.core.engine.openai.temperature import Temperature
from askai.core.enums.routing_model import RoutingModel
from askai.core.model.model_result import ModelResult
from askai.core.support.langchain_support import lc_llm
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.object_mapper import object_mapper
from langchain_core.prompts import PromptTemplate


class ModelSelector(metaclass=Singleton):
    """TODO"""

    INSTANCE: "ModelSelector"

    @property
    def model_template(self) -> PromptTemplate:
        """Retrieve the Routing Model Template."""
        return PromptTemplate(
            input_variables=["datetime", "models", "question"], template=prompt.read_prompt("model-select.txt")
        )

    def select_model(self, query: str) -> ModelResult:
        """Select the response model."""

        final_prompt: str = self.model_template.format(
            datetime=geo_location.datetime, models=RoutingModel.enlist(), question=query
        )
        llm = lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
        if response := llm.invoke(final_prompt):
            json_string: str = response.content  # from AIMessage
            model_result: ModelResult | str = object_mapper.of_json(json_string, ModelResult)
            model_result: ModelResult = model_result if isinstance(model_result, ModelResult) else ModelResult.default()
        else:
            model_result: ModelResult = ModelResult.default()

        return model_result


assert (selector := ModelSelector().INSTANCE) is not None
