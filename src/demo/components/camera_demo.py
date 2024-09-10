import os
from textwrap import dedent

from clitt.core.term.cursor import cursor
from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.tools.text_tools import strip_escapes

from askai.core.component.camera import camera
from askai.core.component.image_store import ImageMetadata, store
from askai.core.features.router.tools.terminal import open_command
from utils import init_context

MENU = dedent(
    f"""Camera Demo options
{'-' * 30}

1. Take a photo
2. Identify person
3. Query a photo
4. Query a face
5. Re-sync images
6. Import images
7. List images

> """
)


if __name__ == "__main__":
    init_context("camera-demo")
    photo: ImageMetadata
    while opt := line_input(MENU, placeholder="Select an option"):
        cursor.write()
        if opt == "1" and (name := strip_escapes(line_input("Photo name: "))):
            pic_file, pic_data = camera.capture(name)
            face_files, face_datas = camera.detect_faces(pic_data, name)
            cursor.write()
            cursor.write(f"Photo taken: {pic_file} Detected faces: {len(face_files)}")
        if opt == "2" and not (name := line_input("Press [Enter] key when ready")):
            if photo := camera.identify():
                cursor.write()
                cursor.write(f"Identified person: {photo.caption} URI: {photo.uri} DIST: {photo.distance}")
                open_command(photo.uri)
            else:
                cursor.write()
                cursor.write("No identification was possible!")
        while opt == "3" and (query := line_input("Query photo: ", "Type in the description (<empty> to return)")):
            cursor.write()
            cursor.write(f"Showing result for: {query}")
            results: list[ImageMetadata] = store.query_image(query)
            for photo in results:
                cursor.write()
                cursor.write(f"Showing photo: {photo.caption} URI: {photo.uri} DIST: {photo.distance}")
                open_command(photo.uri)
        while opt == "4" and (query := line_input("Query face: ", "Type in the description (<empty> to return)")):
            cursor.write()
            cursor.write(f"Showing result for: {query}")
            results: list[ImageMetadata] = store.query_face(query)
            for photo in results:
                cursor.write()
                cursor.write(f"Showing face: {photo.caption} URI: {photo.uri} DIST:", photo.distance)
                open_command(photo.uri)
        if opt == "5":
            count: int = store.sync_store(re_caption=False)
            cursor.write()
            cursor.write(f"Synchronized files: {count}")
        if opt == "6" and (query := line_input("Path to import: ", "File, folder path or glob")):
            images, faces = camera.import_images(query.strip(), True)
            cursor.write()
            cursor.write(f"Imported images: {images} Detected faces: {faces}")
        if opt == "7":
            print(f"```json\n{os.linesep.join(store.enlist())}\n```")
        cursor.write(os.linesep)
    cursor.write("Done")
