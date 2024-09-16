from askai.core.askai_configs import configs
from askai.core.component.camera import camera
from askai.core.features.tools.vision import image_captioner, parse_caption
from askai.core.support.utilities import display_text
from hspylib.core.tools.text_tools import ensure_endswith, ensure_startswith
from os.path import basename
from textwrap import indent

import os


def webcam_capturer(photo_name: str | None, detect_faces: bool = False) -> str:
    """Capture a photo using the webcam and save it locally. Optionally detect faces in the photo.
    :param photo_name: The name of the photo file. If None, a default name will be used.
    :param detect_faces: Whether to detect faces in the photo.
    :return: The file path of the saved photo.
    """

    pic_file, pic_data = camera.capture(photo_name, with_caption=False)
    face_description: str | None = None
    ln: str = os.linesep

    if detect_faces:
        face_files, face_datas = camera.detect_faces(pic_data, photo_name)
        faces: int = len(face_files)
        face_description = (
            (
                f"- **Faces:** `({faces})`\n"
                + indent(f"- {'- '.join([f'`{ff.img_path}` {ln}' for ff in face_files])}", "    ")
                + f"- **Face-Captions:** `({faces})`\n"
                + indent(
                    f"- {'- '.join([f'*{basename(ff.img_path)}*: `{ff.img_caption}` {ln}' for ff in face_files])}",
                    "    ",
                )
            )
            if faces
            else ""
        )

    image_description: str = parse_caption(image_captioner(pic_file.img_path))

    # fmt: off
    return ensure_endswith(ensure_startswith(
        f"\n>   Photo Taken -> {pic_file.img_path}\n\n"
        f"{image_description or ''}\n"
        f"{face_description or ''}", "\n"
    ), "\n")  # fmt: on


def webcam_identifier(max_distance: int = configs.max_id_distance) -> str:
    """Identifies the person in front of the webcam and provides a description of them.
    :param max_distance: The maximum distance for identifying the person based on image similarity.
    :return: A description of the identified person.
    """
    identity: str = "%ORANGE%  No identification was possible!%NC%"
    display_text("Look at the camera...")
    if photo := camera.identify(3, max_distance):
        # fmt: off
        identity = ensure_endswith(ensure_startswith(
            f"\n>   Person Identified -> {photo.uri}\n\n"
            f"- **Distance:** `{round(photo.distance, 4):.4f}/{round(max_distance, 4):.4f}`\n"
            f"{photo.caption}", "\n"
        ), "\n")  # fmt: on

    return identity
