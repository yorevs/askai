#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine.openai
      @file: openai_vision.py
   @created: Tue, 5 Sep 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from typing import TypeAlias, Literal
import os

from langchain_core.prompts import PromptTemplate
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.preconditions import check_argument
from hspylib.core.tools.commons import file_is_not_empty
from langchain.chains.transform import TransformChain
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import chain
from langchain_openai import ChatOpenAI

from askai.core.askai_prompt import prompt
from askai.core.model.image_result import ImageResult
from askai.core.model.screenshot_result import ScreenshotResult
from askai.core.support.utilities import encode_image, find_file

Base64Image: TypeAlias = dict[str, str]

MessageContent: TypeAlias = str | list[str] | dict


class OpenAIVision:
    """Provide a base class for OpenAI vision features. This class implements the AIVision protocol."""

    @staticmethod
    def _encode_image(inputs: dict) -> dict[str, str]:
        """Load an image from file and encode it as a base64 string.
        :param inputs: Dictionary containing the file path under a specific key.
        :return: Dictionary with the base64 encoded image string.
        """
        image_path = inputs["image_path"]
        check_argument(file_is_not_empty(image_path))
        image_base64: str = encode_image(image_path)
        return {"image": image_base64}

    @staticmethod
    @chain
    def create_image_caption_chain(inputs: dict) -> MessageContent:
        """Invoke the image caption chain with image and prompt to generate a caption.
        :param inputs: Dictionary containing the image and prompt information.
        :return: MessageContent object with the generated caption.
        """
        model: BaseChatModel = ChatOpenAI(model="gpt-4o-mini")
        msg: BaseMessage = model.invoke(
            [
                HumanMessage(
                    content=[
                        {"type": "text", "text": inputs["prompt"]},
                        {"type": "text", "text": inputs["parser_guides"]},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{inputs['image']}"}},
                    ]
                )
            ]
        )
        return msg.content

    def image_template(self, question: str = "") -> str:
        return PromptTemplate(input_variables=["question"], template=prompt.read_prompt("img-caption")).format(
            question=question
        )

    def screenshot_template(self, question: str = "") -> str:
        return PromptTemplate(input_variables=["question"], template=prompt.read_prompt("ss-caption")).format(
            question=question
        )

    def caption(
        self,
        filename: AnyPath,
        load_dir: AnyPath | None,
        query: str | None = None,
        image_type: Literal["photo", "screenshot"] = "photo",
    ) -> str:
        """Generate a caption for the provided image.
        :param filename: File name of the image for which the caption is to be generated.
        :param load_dir: Optional directory path for loading related resources.
        :param query: Optional question about details of the image.
        :param image_type: The type of the image to be captioned; one of 'photo' or 'screenshot'.
        :return: A string containing the generated caption.
        """
        final_path: str = os.path.join(load_dir, filename) if load_dir else os.getcwd()
        check_argument(len((final_path := str(find_file(final_path) or ""))) > 0, f"Invalid image path: {final_path}")
        vision_prompt: str = self._get_vision_prompt(query, image_type)
        load_image_chain = TransformChain(
            input_variables=["image_path", "parser_guides"], output_variables=["image"], transform_cb=self._encode_image
        )
        out_parser: JsonOutputParser = self._get_out_parser(image_type)
        vision_chain = load_image_chain | self.create_image_caption_chain | out_parser
        args: dict[str, str] = {
            "image_path": f"{final_path}",
            "prompt": vision_prompt,
            "parser_guides": out_parser.get_format_instructions(),
        }
        return str(vision_chain.invoke(args))

    def _get_out_parser(self, image_type: Literal["photo", "screenshot"]) -> JsonOutputParser:
        """TODO"""
        match image_type:
            case "photo":
                return JsonOutputParser(pydantic_object=ImageResult)
            case "screenshot":
                return JsonOutputParser(pydantic_object=ScreenshotResult)
            case _:
                raise ValueError(f"Parser not found for: {image_type}")

    def _get_vision_prompt(self, query: str, image_type: Literal["photo", "screenshot"]) -> str:
        """TODO"""
        match image_type:
            case "photo":
                return self.image_template(query)
            case "screenshot":
                return self.screenshot_template(query)
            case _:
                raise ValueError(f"Prompt not found for: {image_type}")
