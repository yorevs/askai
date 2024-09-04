from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.component.cache_service import PICTURE_DIR
from askai.core.engine.ai_vision import AIVision
from askai.core.features.validation.accuracy import resolve_x_refs
from askai.core.model.image_result import ImageResult
from askai.core.support.shared_instances import shared
from hspylib.core.config.path_object import PathObject
from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.metaclass.classpath import AnyPath
from PIL import Image
from textwrap import indent
from transformers import BlipForConditionalGeneration, BlipProcessor

import os
import torch


def offline_captioner(path_name: AnyPath) -> str:
    """This tool is used to describe an image.
    :param path_name: The path of the image to describe.
    """

    class HFModel(Enumeration):
        """Available Hugging Face models"""

        # fmt: off
        SF_BLIP_BASE            = "Salesforce/blip-image-captioning-base"
        SF_BLIP_LARGE           = "Salesforce/blip-image-captioning-large"
        # fmt: on

        @staticmethod
        def default() -> "HFModel":
            """Return the default HF model."""
            return HFModel.SF_BLIP_LARGE

    caption: str = "Not available"

    posix_path: PathObject = PathObject.of(path_name)
    if not posix_path.exists:
        # Attempt to resolve cross-references
        if history := str(shared.context.flat("HISTORY") or ""):
            if (x_referenced := resolve_x_refs(path_name, history)) and x_referenced != shared.UNCERTAIN_ID:
                x_ref_path: PathObject = PathObject.of(x_referenced)
                posix_path: PathObject = x_ref_path if x_ref_path.exists else posix_path

    if posix_path.exists:
        events.reply.emit(message=msg.describe_image(str(posix_path)))
        hf_model: HFModel = HFModel.default()
        # Use GPU if it's available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        image = Image.open(str(posix_path)).convert("RGB")
        model = BlipForConditionalGeneration.from_pretrained(hf_model.value).to(device)
        processor = BlipProcessor.from_pretrained(hf_model.value)
        inputs = processor(images=image, return_tensors="pt").to(device)
        outputs = model.generate(**inputs)
        caption = processor.decode(outputs[0], skip_special_tokens=True)
        caption = caption.title() if caption else "I could not caption the image"

    return caption


def image_captioner(path_name: AnyPath, load_dir: AnyPath | None = None) -> str:
    """This tool is used to describe an image.
    :param path_name: The path of the image to describe.
    :param load_dir: Optional directory path for loading related resources.
    :return: A string containing the description of the image, or None if the description could not be generated.
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
        events.reply.emit(message=msg.describe_image(str(posix_path)), verbosity="debug")
        vision: AIVision = shared.engine.vision()
        caption = vision.caption(posix_path.filename, load_dir or posix_path.abs_dir or PICTURE_DIR)

    return caption


def parse_caption(image_caption: str) -> str:
    """Parse the given image caption.
    :param image_caption: The caption to parse.
    :return: The parsed caption as a string.
    """
    if image_caption:
        result: ImageResult = ImageResult.of(image_caption)
        ln: str = os.linesep
        people_desc: str = ""
        if result.people_description:
            people_desc: str = f"- **People:** `({result.people_count})`\n" + indent(
                f"- {'- '.join([f'`{ppl}{ln}`' for ppl in result.people_description])}", "    "
            )
        return (
            f"- **Description:** `{result.env_description}`\n"
            f"- **Objects:** `{', '.join(result.main_objects)}`\n"
            f"{people_desc or ''}"
        )

    return msg.no_caption()
