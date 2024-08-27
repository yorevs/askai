import os
from os.path import basename
from textwrap import dedent, indent

import pause
from clitt.core.term.cursor import cursor

from askai.core.askai_configs import configs
from askai.core.component.camera import camera
from askai.core.support.utilities import display_text


def webcam_capturer(photo_name: str | None, detect_faces: bool = False) -> str:
    """This tool is used to take a photo (and save it locally) using the webcam. It also provide a captioning
    of the image taken.
    :param photo_name: The name of the photo file.
    :param detect_faces: Whether to detect all faces in the photo.
    """

    pic_file, pic_data = camera.capture(photo_name)
    face_desc: str | None = None
    ln: str = os.linesep

    if detect_faces:
        face_files, face_datas = camera.detect_faces(pic_data, photo_name)
        faces: int = len(face_files)
        face_desc = dedent(
            f"3. Faces Detected ({faces}): \n" +
            indent(
                f"- {'- '.join([ff.img_path + ln for ff in face_files])}", '    ') +
            f"4. Face Captions ({faces}): \n" +
            indent(
                f"- {'- '.join([basename(ff.img_path) + ': ' + ff.img_caption + ln for ff in face_files])}", '    ')
        ).strip()

    caption = dedent(
        f">   Photo Taken\n\n"
        f"1. Location: {pic_file.img_path}\n"
        f"2. Caption: {pic_file.img_caption}\n"
        f"{face_desc}").strip()

    return caption


def webcam_identifier(max_distance: int = configs.max_id_distance) -> str:
    """This too is used to identify the person in front of the webcam. It also provide a description of him/her."""
    identity: str = "%ORANGE%  No identification was possible!%NC%"
    display_text("Look at the camera...")
    pause.seconds(2)
    display_text("GO  ")
    pause.seconds(1)
    cursor.erase_line()
    cursor.erase_line()
    if photo := camera.identify(max_distance):
        identity = dedent(f"""
            >   Person Identified:

            - **Caption:** `{photo.caption}`
            - **Distance:** `{round(photo.distance, 4):.4f}/{round(max_distance, 4):.4f}`
            - **URI:** `{photo.uri}`""")

    return identity
