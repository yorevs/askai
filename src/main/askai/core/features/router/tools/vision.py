from typing import Optional

import torch
from PIL import Image
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.features.validation.accuracy import resolve_x_refs
from askai.core.support.shared_instances import shared
from hspylib.core.config.path_object import PathObject
from hspylib.core.enums.enumeration import Enumeration
from transformers import BlipForConditionalGeneration, BlipProcessor


def image_captioner(path_name: str) -> Optional[str]:
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
        def default() -> 'HFModel':
            """Return the default HF model."""
            return HFModel.SF_BLIP_LARGE

    caption: str = 'Not available'

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
        caption = caption.title() if caption else 'I could not caption the image'

    return caption
