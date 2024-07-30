import os
from textwrap import dedent

from matplotlib import pyplot as plt

from askai.core.component.camera import camera
from askai.core.component.recognizer import recognizer
from utils import init_context

MENU = dedent("""
1. Take a photo
2. Identify person
3. Query a photo
4. Query a face
5. Re-sync images
6. List images
? """)


if __name__ == "__main__":
    init_context("camera-demo")
    while opt := input(MENU):
        print()
        while opt == '1' and (name := input("Photo name: ")):
            pic_file, pic_data = camera.capture(name, countdown=3)
            face_files, face_datas = camera.detect_faces(pic_data, name, caption_faces=True)
            print(os.linesep, "Photo taken: ", pic_file, 'Detected faces: ', len(face_files))
        while opt == '2' and not (name := input("Press [Enter] key when ready")):
            if person := camera.identify():
                print(os.linesep, "Person photo: ", person.uri)
                plt.imshow(person.data)
                plt.axis("off")
                plt.show()
            else:
                print(os.linesep, "No identification was possible!")
        while opt == '3' and (query := input("Query photo: ")):
            print(os.linesep, "Showing result for:", query)
            results = recognizer.query_photo(query)
            for photo in results:
                print(os.linesep, 'Showing photo: ', f'"{photo.name}"', 'URI: ', photo.uri, 'DIST:', photo.distance)
                plt.imshow(photo.data)
                plt.axis("off")
                plt.show()
        while opt == '4' and (query := input("Query face: ")):
            print(os.linesep, "Showing result for:", query)
            results = recognizer.query_face(query)
            for face in results:
                print(os.linesep, 'Showing face: ', face.name, 'URI: ', face.uri, 'DIST:', face.distance)
                plt.imshow(face.data)
                plt.axis("off")
                plt.show()
        if opt == '5':
            recognizer.sync_store(caption_enable=True)
        if opt == '6':
            print(os.linesep.join(recognizer.enlist()))
        print()
    print(os.linesep, 'Done')

