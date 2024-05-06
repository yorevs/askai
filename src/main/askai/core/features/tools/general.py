#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.tools.general
      @file: general.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

import os

from askai.core.askai_messages import msg


def display_tool(*texts: str) -> str:
    """Display the given texts using markdown.
    :param texts: The list of texts to be displayed.
    """
    output = os.linesep.join(texts)

    return output or msg.translate("Sorry, there is nothing to display")
