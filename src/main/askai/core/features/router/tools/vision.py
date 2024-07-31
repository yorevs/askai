from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.features.validation.accuracy import resolve_x_refs
from askai.core.support.shared_instances import shared
from hspylib.core.config.path_object import PathObject
from PIL import Image
from transformers import BlipForConditionalGeneration, BlipProcessor
from typing import Optional

import torch


def image_captioner(path_name: str) -> Optional[str]:
    """This tool is used to describe an image."""
    caption: str | None = None
    posix_path: PathObject = PathObject.of(path_name)
    if not posix_path.exists:
        # Attempt to resolve cross-references
        if history := str(shared.context.flat("HISTORY") or ""):
            if (x_referenced := resolve_x_refs(path_name, history)) and x_referenced != shared.UNCERTAIN_ID:
                x_ref_path: PathObject = PathObject.of(x_referenced)
                posix_path: PathObject = x_ref_path if x_ref_path.exists else posix_path

    if posix_path.exists:
        events.reply.emit(message=msg.describe_image(str(posix_path)))
        # specify model to be used
        hf_model = "Salesforce/blip-image-captioning-base"
        # use GPU if it's available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # preprocessor will prepare images for the model
        processor = BlipProcessor.from_pretrained(hf_model)
        # then we initialize the model itself
        model = BlipForConditionalGeneration.from_pretrained(hf_model).to(device)
        # download the image and convert to PIL object
        image = Image.open(str(posix_path)).convert("RGB")
        inputs = processor(image, return_tensors="pt").to(device)
        # generate the caption
        out = model.generate(**inputs, max_new_tokens=20)
        # get the caption
        caption = processor.decode(out[0], skip_special_tokens=True)
        caption = caption.title() if caption else 'I dont know'

    return caption
