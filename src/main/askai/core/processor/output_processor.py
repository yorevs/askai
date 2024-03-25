#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processor
      @file: output_processor.py
   @created: Fri, 23 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperatures import Temperatures
from askai.core.model.chat_context import ContextRaw
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor
from askai.core.support.shared_instances import shared
from langchain_core.prompts import PromptTemplate
from typing import Optional, Tuple

import logging as log


class OutputProcessor(AIProcessor):
    """Process command output prompts."""

    def __init__(self):
        super().__init__("output-prompt")

    def query_type(self) -> str:
        return 'OutputQuery'

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        status = False
        commands = "; ".join([c.cmd_line for c in query_response.commands])
        template = PromptTemplate(input_variables=["command_line", "shell"], template=self.template())
        final_prompt: str = msg.translate(template.format(command_line=commands, shell=prompt.shell))
        shared.context.set("SETUP", final_prompt, "system")
        context: ContextRaw = shared.context.join("CONTEXT", "SETUP")
        log.info("Output::[COMMAND] '%s'  context=%s", commands, context)

        if (response := shared.engine.ask(context, *Temperatures.ZERO.value)) and response.is_success:
            log.debug("Output::[RESPONSE] Received from AI: %s.", response)
            if output := response.message:
                shared.context.push("CONTEXT", output, "assistant")
            status = True
        else:
            log.error(f"Output processing failed. CONTEXT=%s  RESPONSE=%s", context, response)
            output = msg.llm_error(response.message)

        return status, output
