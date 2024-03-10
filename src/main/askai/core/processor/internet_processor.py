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
import logging as log
from typing import Tuple, Optional, List

from hspylib.core.zoned_datetime import now
from langchain_core.prompts import PromptTemplate

from askai.core.askai_messages import msg
from askai.core.component.cache_service import cache
from askai.core.component.internet_service import internet
from askai.core.model.query_response import QueryResponse
from askai.core.model.search_result import SearchResult
from askai.core.processor.ai_processor import AIProcessor
from askai.core.support.object_mapper import object_mapper
from askai.core.support.shared_instances import shared


class InternetProcessor(AIProcessor):
    """Process generic prompts."""

    def __init__(self):
        super().__init__('internet-prompt', 'internet-persona')

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        status = False
        output = None
        template = PromptTemplate(input_variables=['cur_date'], template=self.template())
        final_prompt: str = msg.translate(template.format(cur_date=now('%a %d %b %Y')))
        shared.context.set("SETUP", final_prompt, 'system')
        shared.context.set("QUESTION", query_response.question)
        context: List[dict] = shared.context.get_many("SETUP", "QUESTION")
        log.info("Setup::[INTERNET] '%s'  context=%s", query_response.question, context)
        try:
            if not (response := cache.read_reply(query_response.question)):
                if (response := shared.engine.ask(context, temperature=0.0, top_p=0.0)) and response.is_success:
                    search_result: SearchResult = object_mapper.of_json(response.message, SearchResult)
                    if results := internet.search(search_result.query):
                        search_result.results = results
                        output = str(search_result)
                        shared.context.set("INTERNET", output, 'assistant')
                        cache.save_reply(query_response.question, output)
                        status = True
                else:
                    output = msg.llm_error(response.message)
            else:
                log.debug('Reply found for "%s" in cache.', query_response.question)
                output = response
                shared.context.set("INTERNET", output, 'assistant')
                status = True
        except Exception as err:
            output = msg.llm_error(str(err))
        finally:
            return status, output
