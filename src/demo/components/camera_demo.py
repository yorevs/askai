from askai.core.component.image_store import ImageMetadata, store
from askai.core.component.multimedia.camera import camera
from askai.core.router.tools.terminal import open_command
from clitt.core.term.cursor import cursor
from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.tools.text_tools import strip_escapes
from textwrap import dedent
from utils import init_context

import os

min_distance = 1.6

# fmt: off
MENU = dedent(f"""\
> Camera Demo options

1. Take a photo
2. Identify person
3. Query a photo
4. Query a face
5. Re-sync images
6. Import images
7. List images

$ """)
# fmt: on


if __name__ == "__main__":
    init_context("camera-demo")
    photo: ImageMetadata
    while opt := line_input(MENU, placeholder="Select an option", markdown=True):
        cursor.writeln()
        if opt == "1" and (name := strip_escapes(line_input("Photo name: "))):
            pic_file, pic_data = camera.capture(name)
            face_files, face_datas = camera.detect_faces(pic_data, name)
            cursor.writeln()
            cursor.writeln(f"Photo taken: {pic_file} Detected faces: {len(face_files)}")
        if opt == "2" and not (name := line_input("Press [Enter] key when ready")):
            if photo := camera.identify():
                cursor.writeln()
                cursor.writeln(f"Identified person: {photo.caption} URI: {photo.uri} DIST: {photo.distance}")
                open_command(photo.uri)
            else:
                cursor.writeln()
                cursor.writeln("No identification was possible!")
        while opt == "3" and (query := line_input("Query photo: ", "Type in the description (<empty> to return)")):
            cursor.writeln()
            cursor.writeln(f"Showing results for: {query}")
            results: list[ImageMetadata] = store.query_image(query)
            # Filtering by distances less than 0.7
            for photo in list(filter(lambda r: r.distance <= min_distance, results)):
                cursor.writeln()
                cursor.writeln(f"Showing photo: {photo.caption} URI: {photo.uri} DIST: {photo.distance}")
                open_command(photo.uri)
            cursor.writeln()
        while opt == "4" and (query := line_input("Query face: ", "Type in the description (<empty> to return)")):
            cursor.writeln()
            cursor.writeln(f"Showing results for: {query}")
            results: list[ImageMetadata] = store.query_face(query)
            # Filtering by distances less than 0.7
            for photo in list(filter(lambda r: r.distance <= min_distance, results)):
                cursor.writeln()
                cursor.writeln(f"Showing face: {photo.caption} URI: {photo.uri} DIST: {photo.distance}")
                open_command(photo.uri)
            cursor.writeln()
        if opt == "5":
            count: int = store.sync_store(re_caption=False)
            cursor.writeln()
            cursor.writeln(f"Synchronized files: {count}")
        if opt == "6" and (query := line_input("Path to import: ", "File, folder path or glob")):
            images, faces = camera.import_images(query.strip(), True)
            cursor.writeln()
            cursor.writeln(f"Imported images: {images} Detected faces: {faces}")
        if opt == "7":
            print(f"```json\n{os.linesep.join(store.enlist())}\n```")
        cursor.writeln(os.linesep)
    cursor.writeln("Done")
