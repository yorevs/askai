#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.support.langchain_support
      @file: langchain_support.py
   @created: Fri, 28 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.support.shared_instances import shared
from functools import lru_cache
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_not_none
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel, BaseLLM


class LangChainSupport(metaclass=Singleton):
    """Helper class to support the use of langchain framework."""

    INSTANCE: "LangChainSupport"

    @staticmethod
    @lru_cache
    def create_model(temperature: float = 0.0, top_p: float = 0.0) -> BaseLLM:
        """Create a LangChain LLM model instance using the current AI engine.
        :param temperature: The temperature setting for the LLM model, which controls the randomness of the output.
        :param top_p: The top-p setting for the LLM model, which controls the diversity of the output by limiting the
                      cumulative probability of token selection.
        :return: An instance of the LLM model.
        """
        check_not_none(shared.engine, "AI Engine was not created yet!")
        return shared.engine.lc_model(temperature, top_p)

    @staticmethod
    @lru_cache
    def create_chat_model(temperature: float = 0.0) -> BaseChatModel:
        """Create a LangChain LLM chat model instance using the current AI engine.
        :param temperature: The temperature setting for the LLM chat model, which controls the randomness of the
                            responses.
        :return: An instance of the LLM chat model.
        """

        check_not_none(shared.engine, "AI Engine was not created yet!")
        return shared.engine.lc_chat_model(temperature)

    @staticmethod
    @lru_cache
    def create_embeddings(model: str = "text-embedding-3-small") -> Embeddings:
        """Create a LangChain LLM embeddings model instance using the current AI engine.
        :param model: The name of the embeddings model to use (default is "text-embedding-3-small").
        :return: An instance of the embeddings model.
        """
        check_not_none(shared.engine, "AI Engine was not created yet!")
        return shared.engine.lc_embeddings(model)


assert (lc_llm := LangChainSupport().INSTANCE) is not None
