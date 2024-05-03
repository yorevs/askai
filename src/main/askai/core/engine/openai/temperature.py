#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine.openai
      @file: temperature.py
   @created: Tue, 23 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from hspylib.core.enums.enumeration import Enumeration


class Temperature(Enumeration):
    """Provide some recommended temperature x top_p combinations for ChatGPT prompts.
    Ref:. https://community.openai.com/t/cheat-sheet-mastering-temperature-and-top-p-in-chatgpt-api/172683

    - Lower temperature (e.g., 0.1 - 0.4): Produces more focused, conservative, and consistent responses.
    This is useful when the marketer needs factual information, precise answers, or messaging that adheres closely
    to a specific format or brand guideline.

    - Moderate temperature (e.g., 0.5 - 0.7): Strikes a balance between creativity and consistency.
    This setting can be useful for general content generation, where a blend of accuracy and inventiveness
    is desired.

    - Higher temperature (e.g., 0.8 - 1.0): Generates more creative, diverse, and unexpected outputs.
    Marketers may prefer this setting when brainstorming innovative campaign ideas, crafting engaging social media
    content, or seeking fresh perspectives on a topic.
    """

    # fmt: off

    COLDEST                     = 0.0, 0.

    # Generates data analysis scripts that are more likely to be correct and efficient. Output is more deterministic
    # and focused.
    DATA_ANALYSIS               = 0.2, 0.1

    # Generates code that adheres to established patterns and conventions. Output is more deterministic and focused.
    # Useful for generating syntactically correct code.
    CODE_GENERATION             = 0.2, 0.1

    # Generates code comments that are more likely to be concise and relevant. Output is more deterministic
    # and adheres to conventions.
    CODE_COMMENT_GENERATION     = 0.3, 0.2

    # Generates conversational responses that balance coherence and diversity. Output is more natural and engaging.
    CHATBOT_RESPONSES           = 0.5, 0.5

    # Generates code that explores alternative solutions and creative approaches. Output is less constrained by
    # established patterns.
    EXPLORATORY_CODE_WRITING    = 0.6, 0.7

    # Generates creative and diverse text for storytelling. Output is more exploratory and less constrained by patterns.
    CREATIVE_WRITING            = 0.7, 0.8

    HOTTEST                     = 1.0, 1.0

    # fmt: on

    @property
    def temp(self) -> float:
        return self.value[0]

    @property
    def top_p(self) -> float:
        return self.value[1]
