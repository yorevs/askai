#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processor
      @file: generic_processor.py
   @created: Fri, 23 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor
from askai.core.support.shared_instances import shared
from langchain_core.prompts import PromptTemplate
from typing import List, Optional, Tuple

import logging as log


class GenericProcessor(AIProcessor):
    """Process generic prompts."""

    def __init__(self):
        super().__init__("generic-prompt", "generic-persona")

    def query_desc(self) -> str:
        return (
            "This prompt type is ideal for engaging in casual conversations between you and me, covering a wide range "
            "of everyday topics and general discussions."
        )

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        status = False
        output = None
        template = PromptTemplate(input_variables=["user"], template=self.template())
        final_prompt: str = msg.translate(template.format(user=prompt.user))
        shared.context.set("SETUP", final_prompt, "system")
        shared.context.set("QUESTION", query_response.question)
        context: List[dict] = shared.context.get_many("GENERAL", "SETUP", "QUESTION")
        log.info("Setup::[GENERIC] '%s'  context=%s", query_response.question, context)
        try:
            if (response := shared.engine.ask(context, temperature=1, top_p=1)) and response.is_success:
                output = response.message
                shared.context.push("GENERAL", output, "assistant")
                cache.save_reply(query_response.question, output)
                cache.save_query_history()
                status = True
            else:
                output = msg.llm_error(response.message)
        except Exception as err:
            output = msg.llm_error(str(err))
        finally:
            return status, output
