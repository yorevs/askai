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
from functools import lru_cache
from typing import Tuple

from hspylib.core.metaclass.singleton import Singleton
from langchain_core.prompts import PromptTemplate

from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperatures import Temperatures
from askai.core.model.chat_context import ContextRaw
from askai.core.model.processor_response import ProcessorResponse
from askai.core.support.object_mapper import object_mapper
from askai.core.support.shared_instances import shared


class ProcessorProxy(metaclass=Singleton):
    """TODO"""

    INSTANCE: "ProcessorProxy" = None

    def __init__(self):
        pass

    @lru_cache
    def template(self) -> str:
        return prompt.read_prompt("proxy-prompt")

    def process(self, question: str) -> Tuple[bool, ProcessorResponse]:
        """Return the setup prompt.
        :param question: The question to the AI engine.
        """
        status = False
        template = PromptTemplate(input_variables=[], template=self.template())
        final_prompt = msg.translate(template.format())
        shared.context.set("SETUP", final_prompt)
        shared.context.set("QUESTION", f"\n\nQuestion: {question}\n\nHelpful Answer:")
        context: ContextRaw = shared.context.join("CONTEXT", "SETUP", "QUESTION")
        log.info("Ask::[QUESTION] '%s'  context=%s", question, context)

        if (response := shared.engine.ask(context, *Temperatures.ZERO.value)) and response.is_success:
            log.info("Ask::[PROXY] Received from AI: %s.", str(response))
            output = object_mapper.of_json(response.message, ProcessorResponse)
            if not isinstance(output, ProcessorResponse):
                log.error(msg.invalid_response(output))
                output = response.message
            else:
                status = True
        else:
            output = ProcessorResponse(question=question, terminating=True, response=response.message)

        return status, output


assert (proxy := ProcessorProxy().INSTANCE) is not None
