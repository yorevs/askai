#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.tools.browser
      @file: browser.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.geo_location import geo_location
from askai.core.component.internet_service import internet
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.search_result import SearchResult
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from hspylib.core.object_mapper import object_mapper
from langchain_core.prompts import PromptTemplate
from typing import Optional

import logging as log


def browse(query: str) -> Optional[str]:
    """Fetch the information from the Internet.
    :param query: The search query.
    """
    template = PromptTemplate(
        input_variables=["idiom", "datetime", "location", "question"], template=prompt.read_prompt("search-builder")
    )
    final_prompt: str = template.format(
        idiom=shared.idiom, datetime=geo_location.datetime, location=geo_location.location, question=query
    )
    log.info("Browser::[QUESTION] '%s'  context=''", final_prompt)
    llm = lc_llm.create_chat_model(Temperature.DATA_ANALYSIS.temp)
    response: str = llm.invoke(final_prompt).content

    if response and shared.UNCERTAIN_ID not in response:
        search: SearchResult = object_mapper.of_json(response, SearchResult)
        if not isinstance(search, SearchResult):
            log.error(msg.invalid_response(search))
            output = response.strip()
        else:
            output = internet.search_google(search)
            if not output:
                output = msg.search_empty()
    else:
        output = "Sorry, I don't know."

    return output
