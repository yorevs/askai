#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processor
      @file: processor_proxy.py
   @created: Fri, 23 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import logging as log
from functools import cached_property
from typing import Tuple, List

from hspylib.core.metaclass.singleton import Singleton
from langchain_core.prompts import PromptTemplate

from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.object_mapper import ObjectMapper
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor
from askai.core.support.shared_instances import shared


class ProcessorProxy(metaclass=Singleton):
    """TODO"""

    INSTANCE: 'ProcessorProxy' = None

    def __init__(self):
        self._query_types: str = AIProcessor.find_query_types()

    @cached_property
    def template(self) -> str:
        return prompt.read_prompt('proxy-prompt', 'proxy-persona')

    @property
    def query_types(self) -> str:
        return self._query_types

    def process(self, question: str) -> Tuple[bool, QueryResponse]:
        """Return the setup prompt.
        :param question: The question to the AI engine.
        """
        status = False
        template = PromptTemplate(
            input_variables=[], template=self.template
        )
        final_prompt = template.format(query_types=self.query_types)
        shared.context.set("SETUP", final_prompt, 'system')
        shared.context.set("QUESTION", question)
        context: List[dict] = shared.context.get_many("CONTEXT", "SETUP", "QUESTION")
        log.info("Ask::[QUESTION] '%s'  context=%s", question, context)
        if (response := shared.engine.ask(context, temperature=0.0, top_p=0.0)) and response.is_success:
            log.info('Ask::[PROXY] Received from AI: %s.', str(response))
            output = ObjectMapper.INSTANCE.of_json(response.message, QueryResponse)
            if not isinstance(output, QueryResponse):
                log.error(msg.invalid_response(output))
                output = QueryResponse(question=question, terminating=True, response=response.message)
            else:
                status = True
        else:
            output = QueryResponse(question=question, terminating=True, response=response.message)

        return status, output


assert (proxy := ProcessorProxy().INSTANCE) is not None
