import os
from textwrap import dedent

from matplotlib import pyplot as plt

from askai.core.component.camera import camera, ImageFile
from utils import init_context

MENU = dedent("""
1. Take a photo
2. Identify person
3. Query a photo
4. Query a face
? """)


if __name__ == "__main__":
    init_context("camera-demo")
    while opt := input(MENU):
        print()
        while opt == '1' and (name := input("Photo name: ")):
            f_path, pic = camera.shot(name, countdown=3)
            f_files: set[ImageFile] = camera.detect_faces(pic, name)
            print(os.linesep, "Photo taken: ", f_path, 'Detected faces: ', len(f_files))
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
            results = camera.query_photo(query)
            for photo in results:
                print(os.linesep, 'Showing photo: ', photo.name, 'URI: ', photo.uri, 'DIST:', photo.distance)
                plt.imshow(photo.data)
                plt.axis("off")
                plt.show()
        while opt == '4' and (query := input("Query face: ")):
            print(os.linesep, "Showing result for:", query)
            results = camera.query_face(query)
            for face in results:
                print(os.linesep, 'Showing face: ', face.name, 'URI: ', face.uri, 'DIST:', face.distance)
                plt.imshow(face.data)
                plt.axis("off")
                plt.show()
        print()
    print(os.linesep, 'Done')

