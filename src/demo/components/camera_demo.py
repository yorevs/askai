import os
from textwrap import dedent

from matplotlib import pyplot as plt

from askai.core.component.camera import camera
from askai.core.component.image_store import store, ImageMetadata
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
    photo: ImageMetadata
    while opt := input(MENU):
        print()
        while opt == '1' and (name := input("Photo name: ")):
            pic_file, pic_data = camera.capture(name)
            face_files, face_datas = camera.detect_faces(pic_data, name)
            print()
            print("Photo taken: ", pic_file, 'Detected faces: ', len(face_files))
        if opt == '2' and not (name := input("Press [Enter] key when ready")):
            if photo := camera.identify():
                print()
                print("Identified person: ", f'"{photo.name}"', 'URI: ', photo.uri, 'DIST:', photo.distance)
                plt.imshow(photo.data)
                plt.axis("off")
                plt.show()
            else:
                print()
                print("No identification was possible!")
        while opt == '3' and (query := input("Query photo: ")):
            print()
            print("Showing result for:", query)
            results: list[ImageMetadata] = store.query_photo(query)
            for photo in results:
                print()
                print('Showing photo: ', f'"{photo.name}"', 'URI: ', photo.uri, 'DIST:', photo.distance)
                plt.imshow(photo.data)
                plt.axis("off")
                plt.show()
        while opt == '4' and (query := input("Query face: ")):
            print()
            print("Showing result for:", query)
            results: list[ImageMetadata] = store.query_face(query)
            for photo in results:
                print()
                print('Showing face: ', photo.name, 'URI: ', photo.uri, 'DIST:', photo.distance)
                plt.imshow(photo.data)
                plt.axis("off")
                plt.show()
        if opt == '5':
            store.sync_store(with_caption=False)
        if opt == '6':
            print(os.linesep.join(store.enlist()))
        print()
        print()
    print('Done')

