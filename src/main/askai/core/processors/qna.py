#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processors.qna
      @file: qna.py
   @created: Fri, 5 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.component.summarizer import summarizer
from askai.core.model.ai_reply import AIReply
from askai.core.model.summary_result import SummaryResult
from askai.exception.exceptions import TerminatingQuery
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_state
from typing import Optional


class QnA(metaclass=Singleton):
    """Processor to provide a questions and answers session about a summarized context."""

    INSTANCE: "QnA"

    def process(self, question: str, **_) -> Optional[str]:
        """Process the user question against a summarized context to retrieve answers.
        :param question: The user question to process.
        """

        if not question:
            raise TerminatingQuery("The user wants to exit!")
        if question.casefold() in ["exit", "leave", "quit", "q"] or not (response := summarizer.query(question)):
            events.reply.emit(reply=AIReply.info(msg.leave_qna()))
            events.mode_changed.emit(mode="DEFAULT")
            return None

        check_state(isinstance(response[0], SummaryResult))
        output = response[0].answer

        return output


assert (qna := QnA().INSTANCE) is not None
