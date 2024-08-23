import os
from os.path import basename
from textwrap import dedent, indent

from askai.core.component.camera import camera


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

