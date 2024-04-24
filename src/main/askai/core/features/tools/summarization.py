#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.tools.summarization
      @file: summarization.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.component.summarizer import summarizer
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text
from askai.exception.exceptions import DocumentsNotFound
from hspylib.core.tools.text_tools import ensure_startswith
from typing import Optional

import logging as log
import os


def summarize(base_folder: str, glob: str) -> Optional[str]:
    """Summarize files and folders.
    :param base_folder: The base folder to be summarized.
    :param glob: The glob to match the files to be summarized.
    """
    try:
        glob = ensure_startswith(glob, "**/")
        if not summarizer.exists(base_folder, glob):
            if not summarizer.generate(base_folder, glob):
                return msg.summary_not_possible()
        else:
            summarizer.folder = base_folder
            summarizer.glob = glob
            log.info("Reusing persisted summarized content: '%s/%s'", base_folder, glob)
        output = _qna()
    except (FileNotFoundError, ValueError, DocumentsNotFound) as err:
        output = msg.summary_not_possible(err)

    return output


def _ask_and_reply(question: str) -> Optional[str]:
    """Query the summarized for questions related to the summarized content.
    :param question: the question to be asked to the AI.
    """
    output = None
    if results := summarizer.query(question):
        output = os.linesep.join([r.answer for r in results]).strip()
    return output


def _qna() -> str:
    """Questions and Answers about the summarized content."""
    display_text(
        f"# {msg.enter_qna()} %EOL%" f"> Content:  {summarizer.sum_path} %EOL%%EOL%" f"`{msg.press_esc_enter()}` %EOL%"
    )
    AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.qna_welcome())
    while question := shared.input_text(f"{shared.username}: %GREEN%"):
        if not (output := _ask_and_reply(question)):
            break
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=f"{output}")
    display_text(f"# {msg.leave_qna()} %EOL%")

    return msg.welcome_back()
