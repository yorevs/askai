#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.router.tools.summarization
      @file: summarization.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.component.summarizer import summarizer
from askai.exception.exceptions import DocumentsNotFound
from hspylib.core.tools.text_tools import ensure_startswith

import logging as log


def summarize(base_folder: str, glob: str) -> str:
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
        events.mode_changed.emit(mode="QNA", sum_path=base_folder, glob=glob)
        output = msg.summary_succeeded(base_folder, glob)
    except (FileNotFoundError, ValueError, DocumentsNotFound) as err:
        output = msg.summary_not_possible(err)

    return output
