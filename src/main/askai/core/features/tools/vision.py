from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.features.rag.rag import resolve_x_refs
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
            if x_referenced := resolve_x_refs(path_name, history):
                path_name: PathObject = PathObject.of(x_referenced)
                posix_path: str = str(path_name) if path_name.exists else posix_path

    if posix_path.exists:
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.describe_image(str(posix_path)))
        # specify model to be used
        hf_model = "Salesforce/blip-image-captioning-large"
        # use GPU if it's available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # preprocessor will prepare images for the model
        processor = BlipProcessor.from_pretrained(hf_model)
        # then we initialize the model itself
        model = BlipForConditionalGeneration.from_pretrained(hf_model).to(device)
        # download the image and convert to PIL object
        image = Image.open(str(posix_path)).convert("RGB")
        # preprocess the image
        hf_model = "Salesforce/blip-image-captioning-large"
        inputs = processor(image, return_tensors="pt").to(device)
        # generate the caption
        out = model.generate(**inputs, max_new_tokens=20)
        # get the caption
        caption = processor.decode(out[0], skip_special_tokens=True)
        caption = msg.translate(f"Caption of '{path_name}' => {caption.title() if caption else 'I dont know'}")

    return caption
