import os
from textwrap import indent

from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.component.cache_service import PICTURE_DIR
from askai.core.engine.ai_vision import AIVision
from askai.core.features.validation.accuracy import resolve_x_refs
from askai.core.model.image_result import ImageResult
from askai.core.support.shared_instances import shared
from hspylib.core.config.path_object import PathObject
from hspylib.core.metaclass.classpath import AnyPath


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
        events.reply.emit(message=msg.describe_image(str(posix_path)))
        vision: AIVision = shared.engine.vision()
        caption = vision.caption(posix_path.filename, load_dir or posix_path.abs_dir or PICTURE_DIR)

    return caption


def parse_caption(image_caption: str) -> str:
    """Parse the given image caption.
    :param image_caption: The caption to parse.
    :return: The parsed caption as a string.
    """
    if image_caption:
        result: ImageResult = ImageResult.model_validate_json(image_caption.replace("'", '"'))
        ln: str = os.linesep
        people_desc: str = ''
        if result.people_description:
            people_desc: str = (
                f"- **People ({result.people_count}):**\n"
                + indent(f"- {'- '.join([ppl + ln for ppl in result.people_description])}", "    ")
            )
        return (
            f"- **Description:** `{result.env_description}`\n"
            f"- **Objects:** `{', '.join(result.main_objects)}`\n"
            f"{people_desc or ''}"
        )

    return msg.no_caption()
