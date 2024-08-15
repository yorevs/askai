from abc import ABC
from textwrap import dedent

import pause
from clitt.core.term.cursor import cursor
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.tools.commons import sysout

from askai.core.askai_configs import configs
from askai.core.component.camera import camera
from askai.core.features.router.tools.terminal import open_command
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text


class CameraCmd(ABC):
    """Provides camera command functionalities."""

    @staticmethod
    def capture(filename: AnyPath = None, detect_faces: bool = True, countdown: int = 3) -> None:
        """Take a photo using hte Webcam.
        :param filename: The filename of the photo taken.
        :param detect_faces: Whether to detect faces on the photo or not.
        :param countdown: A countdown to be displayed before the photo is taken.
        """

        if photo := camera.capture(filename, countdown):
            text_formatter.cmd_print(f"Photo taken: %GREEN%{photo[0]}%NC%")
            if detect_faces:
                if len(faces := camera.detect_faces(photo[1], filename)) > 0:
                    text_formatter.cmd_print(f"Faces detected: %GREEN%{len(faces[0])}%NC%")
        else:
            text_formatter.cmd_print("%RED%Unable to take photo!%NC%")

    @staticmethod
    def identify(max_distance: int = configs.max_id_distance) -> None:
        """Identify the person in from of the WebCam.
        :param max_distance: The maximum distance of the face (the lower, the closer to the real face).
        """
        sysout("Look at the camera...", end='')
        pause.seconds(2)
        display_text("GO  ")
        pause.seconds(1)
        cursor.erase_line()
        cursor.erase_line()
        identity: str | None = None
        if photo := camera.identify(max_distance):
            identity = dedent(
                f"""
                >   Person identified:

                - **Name:** `{photo.name}`
                - **Distance:** `{round(photo.distance, 4):.4f}/{round(max_distance, 4):.4f}`
                - **URI:** `{photo.uri}`
                """)
            open_command(photo.uri)
        cursor.erase_line()
        text_formatter.cmd_print(identity or "%ORANGE%  No identification was possible!%NC%")

    @staticmethod
    def import_images(pathname: AnyPath = None, detect_faces: bool = True) -> None:
        """Import image files into the image collection.
        :param pathname: The pathname or glob to be imported.
        :param detect_faces: Whether to detect faces on the images or not.
        """
        imports: tuple[int, ...] = camera.import_images(str(pathname), detect_faces)
        text_formatter.cmd_print(f"`Imports:` {imports[0]}  `Faces:` {imports[1]}")
