from functools import cached_property
from os.path import dirname
from pathlib import Path
import os

import cv2
import numpy as np
import mediapipe as mp
# Path for exported data, numpy arrays
from numpy import ndarray

DATA_PATH: Path = Path(os.path.join(dirname(__file__), 'MP_Data'))
if not DATA_PATH.exists():
    DATA_PATH.mkdir(parents=True, exist_ok=True)


class GestureActionManager:
    # Number of videos worth of data
    NO_SEQUENCES = 30

    # Videos are going to be 30 frames in length
    SEQUENCE_LENGTH = 30

    # Folder start
    START_FOLDER = 30

    def __init__(self):
        self._mp_holistic = mp.solutions.holistic
        self._mp_drawing = mp.solutions.drawing_utils
        self._actions = np.array([
            'maximize', 'minimize', 'grab', 'pointer', 'click', 'next', 'previous', 'dispose'
        ])
        self._sequences = []
        self._labels = []

    @property
    def actions(self) -> ndarray:
        return self._actions

    @cached_property
    def label_map(self) -> dict[int, str]:
        return {label: num for num, label in enumerate(self._actions)}

    def setup_folders(self):
        # Actions that we try to detect
        for action in self.actions:
            action_path: Path = Path(os.path.join(DATA_PATH, action))
            if not action_path.exists():
                action_path.mkdir(parents=True, exist_ok=True)
            for sequence in range(1, self.NO_SEQUENCES + 1):
                os.makedirs(os.path.join(action_path, str(sequence)), exist_ok=True)

    def mediapipe_detection(self, frame, model):
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # COLOR CONVERSION BGR 2 RGB
        image.flags.writeable = False  # Image is no longer writeable
        results = model.process(image)  # Make prediction
        image.flags.writeable = True  # Image is now writeable
        image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # COLOR CONVERSION RGB 2 BGR
        return image, results

    def draw_landmarks(self, image, results):
        self._mp_drawing.draw_landmarks(
            image, results.face_landmarks, self._mp_holistic.FACEMESH_TESSELATION)  # Draw face connections
        self._mp_drawing.draw_landmarks(
            image, results.pose_landmarks, self._mp_holistic.POSE_CONNECTIONS)  # Draw pose connections
        self._mp_drawing.draw_landmarks(
            image, results.left_hand_landmarks,
            self._mp_holistic.HAND_CONNECTIONS)  # Draw left hand connections
        self._mp_drawing.draw_landmarks(
            image, results.right_hand_landmarks,
            self._mp_holistic.HAND_CONNECTIONS)  # Draw right hand connections

    def draw_styled_landmarks(self, image, results):
        # Draw face connections
        self._mp_drawing.draw_landmarks(
            image, results.face_landmarks, self._mp_holistic.FACEMESH_TESSELATION,
            self._mp_drawing.DrawingSpec(color=(80, 110, 10), thickness=1, circle_radius=1),
            self._mp_drawing.DrawingSpec(color=(80, 256, 121), thickness=1, circle_radius=1)
        )
        # Draw pose connections
        self._mp_drawing.draw_landmarks(
            image, results.pose_landmarks, self._mp_holistic.POSE_CONNECTIONS,
            self._mp_drawing.DrawingSpec(color=(80, 22, 10), thickness=2, circle_radius=4),
            self._mp_drawing.DrawingSpec(color=(80, 44, 121), thickness=2, circle_radius=2)
        )
        # Draw left hand connections
        self._mp_drawing.draw_landmarks(
            image, results.left_hand_landmarks, self._mp_holistic.HAND_CONNECTIONS,
            self._mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
            self._mp_drawing.DrawingSpec(color=(121, 44, 250), thickness=2, circle_radius=2)
        )
        # Draw right hand connections
        self._mp_drawing.draw_landmarks(
            image, results.right_hand_landmarks, self._mp_holistic.HAND_CONNECTIONS,
            self._mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=4),
            self._mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
        )

    def extract_keypoints(self, results):
        pose = np.array(
            [[res.x, res.y, res.z, res.visibility] for res in
             results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33 * 4)
        face = np.array(
            [[res.x, res.y, res.z] for res in
             results.face_landmarks.landmark]).flatten() if results.face_landmarks else np.zeros(468 * 3)
        lh = np.array(
            [[res.x, res.y, res.z] for res in
             results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(21 * 3)
        rh = np.array(
            [[res.x, res.y, res.z] for res in
             results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(21 * 3)
        return np.concatenate([pose, face, lh, rh])

    def create_labels_and_features(self):
        for action in self.actions:
            for sequence in np.array(os.listdir(os.path.join(DATA_PATH, action))).astype(int):
                window = []
                for frame_num in range(self.SEQUENCE_LENGTH):
                    res = np.load(os.path.join(DATA_PATH, action, str(sequence), f"{frame_num}.npy"))
                    window.append(res)
                self._sequences.append(window)
                self._labels.append(self.label_map[action])

    def capture_landmarks(self, action: str):
        cap = cv2.VideoCapture(0)
        # Set mediapipe model
        with self._mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
            # Loop through sequences of videos
            for sequence in range(self.START_FOLDER, self.START_FOLDER + self.NO_SEQUENCES):
                # Loop through video length aka sequence length
                for frame_num in range(self.SEQUENCE_LENGTH):
                    ret, frame = cap.read()
                    image, results = self.mediapipe_detection(frame, holistic)
                    self.draw_styled_landmarks(image, results)
                    # Apply wait logic
                    if frame_num == 0:
                        cv2.putText(
                            image, 'STARTING COLLECTION', (120, 200),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 4, cv2.LINE_AA)
                        cv2.putText(
                            image, f'Collecting frames for {action} Video Number {sequence}', (15, 12),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                        # Show to screen
                        cv2.imshow('OpenCV Feed', image)
                        cv2.waitKey(500)
                    else:
                        cv2.putText(
                            image, f'Collecting frames for {action} Video Number {sequence}', (15, 12),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                        # Show to screen
                        cv2.imshow('OpenCV Feed', image)

                    # Extract and save keypoints
                    keypoints = self.extract_keypoints(results)
                    npy_path = os.path.join(DATA_PATH, action, str(sequence), str(frame_num))
                    np.save(npy_path, keypoints)

                    # Break gracefully
                    if cv2.waitKey(10) & 0xFF == ord('q'):
                        break

            cap.release()
            cv2.destroyAllWindows()

    def demo_media_pipe(self):
        cap = cv2.VideoCapture(0)
        # Set mediapipe model
        with self._mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
            while cap.isOpened():
                ret, frame = cap.read()
                image, results = self.mediapipe_detection(frame, holistic)
                self.draw_styled_landmarks(image, results)
                if results:
                    if results.left_hand_landmarks is not None:
                        lm = results.left_hand_landmarks.landmark
                        print('LH: ', len(lm), end=', ')
                    if results.right_hand_landmarks is not None:
                        lm = results.right_hand_landmarks.landmark
                        print('RH: ', len(lm), end=', ')
                    if results.face_landmarks is not None:
                        lm = results.face_landmarks.landmark
                        print('Face: ', len(lm), end=', ')
                    if results.pose_landmarks is not None:
                        lm = results.pose_landmarks.landmark
                        print('Pose: ', len(lm), end=' ')
                print()
                cv2.imshow('OpenCV Feed', image)
                if cv2.waitKey(10) & 0xFF == ord('q'):
                    break
            cap.release()
            cv2.destroyAllWindows()


if __name__ == '__main__':
    gm: GestureActionManager = GestureActionManager()
    gm.demo_media_pipe()
