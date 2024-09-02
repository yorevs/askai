from abc import ABC
from askai.core.askai_configs import configs
from askai.core.component.camera import camera
from askai.core.features.router.tools.webcam import webcam_identifier
from askai.core.support.text_formatter import text_formatter
from hspylib.core.metaclass.classpath import AnyPath


class CameraCmd(ABC):
    """Provides camera command functionalities."""

    @staticmethod
    def capture(filename: AnyPath = None, detect_faces: bool = True, countdown: int = 3) -> None:
        """Take a photo using the webcam.
        :param filename: The filename to save the photo under (optional).
        :param detect_faces: Whether to detect faces in the photo (default is True).
        :param countdown: The countdown in seconds before the photo is taken (default is 3).
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
        """Identify the person in front of the webcam.
        :param max_distance: The maximum allowable distance for face recognition. A lower value means closer matching
                             to the real face (default is configs.max_id_distance).
        """
        text_formatter.cmd_print(webcam_identifier(max_distance))

    @staticmethod
    def import_images(pathname: AnyPath = None, detect_faces: bool = True) -> None:
        """Import image files into the image collection.
        :param pathname: The pathname or glob pattern specifying the images to be imported (optional).
        :param detect_faces: Whether to detect faces in the imported images (default is True).
        """
        imports: tuple[int, ...] = camera.import_images(str(pathname), detect_faces)
        text_formatter.cmd_print(f"`Imports:` {imports[0]}  `Faces:` {imports[1]}")
