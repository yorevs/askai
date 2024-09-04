import os
from os.path import basename
from textwrap import indent

from askai.core.askai_configs import configs
from askai.core.component.camera import camera
from askai.core.features.router.tools.vision import image_captioner, parse_caption
from askai.core.support.utilities import display_text


def webcam_capturer(photo_name: str | None, detect_faces: bool = False) -> str:
    """This tool is used to take a photo (and save it locally) using the webcam. It also provide a captioning
    of the image taken.
    :param photo_name: The name of the photo file.
    :param detect_faces: Whether to detect all faces in the photo.
    """

    pic_file, pic_data = camera.capture(photo_name, with_caption=False)
    face_desc: str | None = None
    ln: str = os.linesep

    if detect_faces:
        face_files, face_datas = camera.detect_faces(pic_data, photo_name)
        faces: int = len(face_files)
        face_desc = (
            f"- **Faces ({faces}):**\n"
            + indent(f"- {'- '.join([ff.img_path + ln for ff in face_files])}", "    ")
            + f"- **Face Captions ({faces}):**\n"
            + indent(f"- {'- '.join([basename(ff.img_path) + ': ' + ff.img_caption + ln for ff in face_files])}",
                     "    ")
        ) if faces else ''

    people_desc: str = parse_caption(image_captioner(pic_file.img_path))

    return (
        f">   Photo Taken -> {pic_file.img_path}\n\n"
        f"{people_desc or ''}"
        f"{face_desc or ''}"
    )


def webcam_identifier(max_distance: int = configs.max_id_distance) -> str:
    """This too is used to identify the person in front of the webcam. It also provide a description of him/her."""
    identity: str = "%ORANGE%  No identification was possible!%NC%"
    display_text("Look at the camera...")
    if photo := camera.identify(3, max_distance):
        identity = (
            f">   Person Identified -> {photo.uri}\n\n"
            f"- **Description:** `{photo.caption}`\n"
            f"- **Distance:** `{round(photo.distance, 4):.4f}/{round(max_distance, 4):.4f}`\n"
        )

    return identity
