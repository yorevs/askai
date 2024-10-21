from abc import ABC
from askai.core.askai_configs import configs
from askai.core.component.camera import camera
from askai.core.router.tools.webcam import webcam_capturer, webcam_identifier
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text
from hspylib.core.metaclass.classpath import AnyPath


class CameraCmd(ABC):
    """Provides camera command functionalities."""

    @staticmethod
    def capture(filename: AnyPath = None, detect_faces: bool = True) -> None:
        """Take a photo using the webcam.
        :param filename: The filename to save the photo under (optional).
        :param detect_faces: Whether to detect faces in the photo (default is True).
        """
        if photo_description := webcam_capturer(filename, detect_faces):
            display_text(photo_description)
        else:
            text_formatter.commander_print("%RED%Unable to take photo!%NC%")

    @staticmethod
    def identify(max_distance: int = configs.max_id_distance) -> None:
        """Identify the person in front of the webcam.
        :param max_distance: The maximum allowable distance for face recognition. A lower value means closer matching
                             to the real face (default is configs.max_id_distance).
        """
        display_text(webcam_identifier(max_distance))

    @staticmethod
    def import_images(pathname: AnyPath = None, detect_faces: bool = True) -> None:
        """Import image files into the image collection.
        :param pathname: The pathname or glob pattern specifying the images to be imported (optional).
        :param detect_faces: Whether to detect faces in the imported images (default is True).
        """
        imports: tuple[int, ...] = camera.import_images(str(pathname), detect_faces)
        text_formatter.commander_print(f"`Imports:` {imports[0]}  `Faces:` {imports[1]}")
