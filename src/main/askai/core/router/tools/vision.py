import os
from textwrap import indent

import pyautogui
import torch
from PIL import Image
from hspylib.core.config.path_object import PathObject
from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.preconditions import check_argument
from transformers import BlipForConditionalGeneration, BlipProcessor

from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.component.cache_service import PICTURE_DIR
from askai.core.engine.ai_vision import AIVision
from askai.core.model.ai_reply import AIReply
from askai.core.model.image_result import ImageResult
from askai.core.router.evaluation import resolve_x_refs
from askai.core.support.shared_instances import shared


class HFModel(Enumeration):
    """Available Hugging Face models"""

    # fmt: off
    SF_BLIP_BASE    = "Salesforce/blip-image-captioning-base"
    SF_BLIP_LARGE   = "Salesforce/blip-image-captioning-large"
    # fmt: on

    @staticmethod
    def default() -> "HFModel":
        """Return the default HF model."""
        return HFModel.SF_BLIP_BASE


def offline_captioner(path_name: AnyPath) -> str:
    """This tool is used to describe an image.
    :param path_name: The path of the image to describe.
    """

    caption: str = "Not available"

    posix_path: PathObject = PathObject.of(path_name)
    if not posix_path.exists:
        # Attempt to resolve cross-references
        if history := str(shared.context.flat("HISTORY") or ""):
            if (x_referenced := resolve_x_refs(path_name, history)) and x_referenced != shared.UNCERTAIN_ID:
                x_ref_path: PathObject = PathObject.of(x_referenced)
                posix_path: PathObject = x_ref_path if x_ref_path.exists else posix_path

    if posix_path.exists:
        events.reply.emit(reply=AIReply.full(msg.describe_image(posix_path)))
        # Use GPU if it's available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        image = Image.open(str(posix_path)).convert("RGB")
        model_id: str = HFModel.default().value
        match model_id.casefold():
            case model if "blip-" in model:
                model = BlipForConditionalGeneration.from_pretrained(model_id).to(device)
                processor = BlipProcessor.from_pretrained(model_id)
            case _:
                raise ValueError(f"Unsupported model: '{model_id}'")
        inputs = processor(images=image, return_tensors="pt").to(device)
        outputs = model.generate(**inputs)
        caption = processor.decode(outputs[0], skip_special_tokens=True)
        caption = caption.title() if caption else "I could not caption the image"

    return caption


def image_captioner(path_name: AnyPath, load_dir: AnyPath | None = None, query: str | None = None) -> str:
    """This tool is used to describe an image.
    :param path_name: The path of the image to describe.
    :param load_dir: Optional directory path for loading related resources.
    :param query: Optional query about the photo taken.
    :return: A string containing the description of the image, or None if the description could not be generated.
    """
    image_caption: str = "Unavailable"
    posix_path: PathObject = PathObject.of(path_name)

    if not posix_path.exists:
        # Attempt to resolve cross-references
        if history := str(shared.context.flat("HISTORY") or ""):
            if (x_referenced := resolve_x_refs(path_name, history)) and x_referenced != shared.UNCERTAIN_ID:
                x_ref_path: PathObject = PathObject.of(x_referenced)
                posix_path: PathObject = x_ref_path if x_ref_path.exists else posix_path

    if posix_path.exists:
        events.reply.emit(reply=AIReply.full(msg.describe_image(posix_path)))
        vision: AIVision = shared.engine.vision()
        image_caption = vision.caption(posix_path.filename, load_dir or posix_path.abs_dir or PICTURE_DIR, query)

    return image_caption


def parse_caption(image_caption: str) -> list[str]:
    """Parse the given image caption.
    :param image_caption: The caption to parse.
    :return: The parsed caption as a string.
    """
    if image_caption:
        result: ImageResult = ImageResult.of(image_caption)
        ln: str = os.linesep
        people_desc: str = ""
        if result.people_description:
            people_desc: list[str] = [
                f"- **People:** `({result.people_count})`",
                indent(f"- {'- '.join([f'`{ppl}{ln}`' + ln for ppl in result.people_description])}", "    "),
            ]
        return [
            f"- **Description:** `{result.env_description}`",
            f"- **Objects:** `{', '.join(result.main_objects)}`",
        ] + people_desc

    return [msg.no_caption()]


def take_screenshot(path_name: AnyPath, load_dir: AnyPath | None = None) -> str:
    """Takes a screenshot and saves it to the specified path.
    :param path_name: The path where the screenshot will be saved.
    :param load_dir: Optional directory to save the screenshot.
    :return: The path to the saved screenshot.
    """

    posix_path: PathObject = PathObject.of(path_name)
    check_argument(os.path.exists(posix_path.abs_dir))
    screenshot = pyautogui.screenshot()
    _, ext = os.path.splitext(posix_path.filename)
    if ext.casefold().endswith((".jpg", ".jpeg")):
        screenshot = screenshot.convert("RGB")
    final_path: str = os.path.join(load_dir or posix_path.abs_dir or PICTURE_DIR, posix_path.filename)
    screenshot.save(final_path)
    events.reply.emit(reply=AIReply.full(msg.screenshot_saved(final_path)))
    desktop_caption = image_captioner(final_path, load_dir)

    return desktop_caption
