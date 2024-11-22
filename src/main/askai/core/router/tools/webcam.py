import os
from os.path import basename
from string import Template
from textwrap import indent

from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.component.camera import camera
from askai.core.model.ai_reply import AIReply
from askai.core.router.tools.vision import image_captioner, parse_image_caption

PHOTO_TEMPLATE: Template = Template(
    """\

>   Photo Taken -> ${pic_file}

${image_description}
${face_description}

"""
)

ID_TEMPLATE: Template = Template(
    """\

>   Person Identified -> ${photo_uri}

- **Distance:** `${distance}`
${photo_caption}

"""
)

CAPTION_TEMPLATE: Template = Template(
    """\

>   Description of `${image_path}`:

${image_caption}

"""
)


def webcam_capturer(photo_name: str | None, detect_faces: bool = False, query: str | None = None) -> str:
    """Capture a photo using the webcam and save it locally. Optionally detect faces in the photo.
    :param photo_name: The name of the photo file. If None, a default name will be used.
    :param detect_faces: Whether to detect faces in the photo.
    :param query: Optional query about the photo taken.
    :return: The file path of the saved photo.
    """

    pic_file, pic_data = camera.capture(photo_name, with_caption=False)
    face_description: list[str] = []
    ln: str = os.linesep

    if detect_faces:
        face_files, face_datas = camera.detect_faces(pic_data, photo_name)
        faces: int = len(face_files)
        face_description: list[str] = (
            [
                f"- **Faces:** `({faces})`",
                indent(f"- {'- '.join([f'`{ff.img_path}` {ln}' for ff in face_files])}", "    "),
                f"- **Face-Captions:** `({faces})`",
                indent(
                    f"- {'- '.join([f'*{basename(ff.img_path)}*: `{ff.img_caption}` {ln}' for ff in face_files])}",
                    "    ",
                ),
            ]
            if faces
            else []
        )

    image_description: list[str] = parse_image_caption(image_captioner(pic_file.img_path, query=query))

    return PHOTO_TEMPLATE.substitute(
        pic_file=pic_file.img_path,
        image_description=os.linesep.join(image_description) if image_description else "",
        face_description=os.linesep.join(face_description) if face_description else "",
    )


def webcam_identifier(max_distance: int = configs.max_id_distance) -> str:
    """Identifies the person in front of the webcam and provides a description of them.
    :param max_distance: The maximum distance for identifying the person based on image similarity.
    :return: A description of the identified person.
    """
    events.reply.emit(reply=AIReply.debug(msg.look_at_camera()))
    if photo := camera.identify(3, max_distance):
        return ID_TEMPLATE.substitute(
            photo_uri=photo.uri,
            distance=f"{round(photo.distance, 4):.4f}/{round(max_distance, 4):.4f}",
            photo_caption=photo.caption,
        )

    return "%ORANGE%  No identification was possible!%NC%"
