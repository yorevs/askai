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
from typing import Tuple, List

from hspylib.core.metaclass.singleton import Singleton
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.model.processor_response import ProcessorResponse
from askai.core.support.langchain_support import lc_llm
from askai.core.support.object_mapper import object_mapper
from askai.core.support.shared_instances import shared


class ProcessorProxy(metaclass=Singleton):
    """TODO
    """

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
        template = PromptTemplate(input_variables=['idiom'], template=self.template())
        final_prompt = template.format(idiom=shared.idiom)
        shared.context.set("SETUP", final_prompt, "system")
        shared.context.set("QUESTION", f"\n\nQuestion: {question}\n\nHelpful Answer:")
        ctx: List[str] = shared.context.flat("CONTEXT", "SETUP", "QUESTION")
        log.info("Proxy::[QUESTION] '%s'  context=%s", question, ctx)

        chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
        chain = create_stuff_documents_chain(lc_llm.create_chat_model(), chat_prompt)
        context = Document(' '.join(ctx))

        if response := chain.invoke({"query": question, "context": [context]}):
            log.info("Proxy::[RESPONSE] Received from AI: %s.", str(response))
            output = object_mapper.of_json(response, ProcessorResponse)
            if not isinstance(output, ProcessorResponse):
                log.error(msg.invalid_response(output))
                output = response
            else:
                status = True
        else:
            output = ProcessorResponse(question=question, terminating=True, response=response)

        return status, output


assert (proxy := ProcessorProxy().INSTANCE) is not None
