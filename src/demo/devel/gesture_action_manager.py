import threading
from functools import cached_property
from os.path import dirname
from pathlib import Path
import os

import cv2
import numpy as np
from keras.src.utils import to_categorical
from mediapipe.python.solutions import drawing_utils
from mediapipe.python.solutions.face_mesh_connections import FACEMESH_TESSELATION
from mediapipe.python.solutions.hands_connections import HAND_CONNECTIONS
from mediapipe.python.solutions.holistic import Holistic
from mediapipe.python.solutions.pose_connections import POSE_CONNECTIONS
from numpy import ndarray

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import TensorBoard
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical

from askai.core.component.audio_player import player

DATA_PATH: Path = Path(os.path.join(dirname(__file__), 'MP_Data'))
if not DATA_PATH.exists():
    DATA_PATH.mkdir(parents=True, exist_ok=True)

LOGS_PATH: Path = Path(os.path.join(dirname(__file__), 'Logs'))
if not LOGS_PATH.exists():
    LOGS_PATH.mkdir(parents=True, exist_ok=True)


class GestureActionManager:
    # Number of sequences of videos
    NUM_VIDEOS = 30

    # Videos are going to be 30 frames in length
    NUM_FRAMES = 30

    #  Start index of the sequences and videos
    START_IDX = 1

    @staticmethod
    def setup_folder(action: str, sequence_num: int) -> None:
        action_path: str = os.path.join(DATA_PATH, action)
        os.makedirs(os.path.join(action_path, str(sequence_num)), exist_ok=True)

    @staticmethod
    def mediapipe_detection(cv2_frame, model):
        image = cv2.cvtColor(cv2_frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = model.process(image)  # Detect
        image.flags.writeable = True
        image = cv2.cvtColor(cv2_frame, cv2.COLOR_RGB2BGR)  # convert to BGR
        return image, results

    @staticmethod
    def draw_landmarks(image, results) -> None:
        drawing_utils.draw_landmarks(
            image, results.face_landmarks, FACEMESH_TESSELATION)  # Draw face connections
        drawing_utils.draw_landmarks(
            image, results.pose_landmarks, POSE_CONNECTIONS)  # Draw pose connections
        drawing_utils.draw_landmarks(
            image, results.left_hand_landmarks,
            HAND_CONNECTIONS)  # Draw left hand connections
        drawing_utils.draw_landmarks(
            image, results.right_hand_landmarks,
            HAND_CONNECTIONS)  # Draw right hand connections

    @staticmethod
    def draw_styled_landmarks(image, results) -> None:
        # Draw face connections
        drawing_utils.draw_landmarks(
            image, results.face_landmarks, FACEMESH_TESSELATION,
            drawing_utils.DrawingSpec(color=(80, 110, 10), thickness=1, circle_radius=1),
            drawing_utils.DrawingSpec(color=(80, 256, 121), thickness=1, circle_radius=1)
        )
        # Draw pose connections
        drawing_utils.draw_landmarks(
            image, results.pose_landmarks, POSE_CONNECTIONS,
            drawing_utils.DrawingSpec(color=(80, 22, 10), thickness=2, circle_radius=4),
            drawing_utils.DrawingSpec(color=(80, 44, 121), thickness=2, circle_radius=2)
        )
        # Draw left hand connections
        drawing_utils.draw_landmarks(
            image, results.left_hand_landmarks, HAND_CONNECTIONS,
            drawing_utils.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
            drawing_utils.DrawingSpec(color=(121, 44, 250), thickness=2, circle_radius=2)
        )
        # Draw right hand connections
        drawing_utils.draw_landmarks(
            image, results.right_hand_landmarks, HAND_CONNECTIONS,
            drawing_utils.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=4),
            drawing_utils.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
        )

    @staticmethod
    def extract_keypoints(results) -> ndarray:
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

    def __init__(self):
        self._actions = np.array([
            'maximize', 'minimize', 'grab', 'pointer', 'click', 'next', 'previous', 'dispose'
        ])
        self._tb_callback = TensorBoard(log_dir=LOGS_PATH)

    @property
    def actions(self) -> ndarray:
        return self._actions

    @cached_property
    def label_map(self) -> dict[str, int]:
        return {label: num for num, label in enumerate(self._actions)}

    def create_sequences_and_labels(self, action: str):
        sequences: list = []
        labels: list = []
        for video_num in np.array(os.listdir(os.path.join(DATA_PATH, action))).astype(int):
            window = []
            for frame_num in range(self.START_IDX, self.NUM_FRAMES + 1):
                res = np.load(os.path.join(DATA_PATH, action, str(video_num), f"{frame_num}.npy"))
                window.append(res)
            sequences.append(window)
            labels.append(self.label_map[action])
        return sequences, labels

    def capture_landmarks(self, action: str):
        assert action in self.actions
        cap = cv2.VideoCapture(0)
        with Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
            for video_num in range(self.START_IDX, self.NUM_VIDEOS + 1):
                for frame_num in range(self.START_IDX, self.NUM_FRAMES + 1):
                    self.setup_folder(action, video_num)
                    ret, frame = cap.read()
                    image, results = self.mediapipe_detection(frame, holistic)
                    self.draw_styled_landmarks(image, results)

                    if frame_num == self.START_IDX:
                        threading.Thread(target=player.play_sfx, args=('beep-new-1s',)).start()
                        cv2.putText(
                            image, 'STARTING COLLECTION', (120, 200),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 4, cv2.LINE_AA)
                        cv2.putText(
                            image, f'Collecting frames for {action} Video Number {video_num}', (15, 12),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                        cv2.imshow('OpenCV Feed', image)
                        cv2.waitKey(1000)
                    else:
                        cv2.putText(
                            image, f'Collecting frames for {action} Video Number {video_num}', (15, 12),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                        cv2.imshow('OpenCV Feed', image)

                    # Extract and save keypoints
                    keypoints = self.extract_keypoints(results)
                    npy_path = os.path.join(DATA_PATH, action, str(video_num), str(frame_num))
                    np.save(npy_path, keypoints)

                    if cv2.waitKey(10) & 0xFF == ord('q'):
                        break

            cap.release()
            cv2.destroyAllWindows()

    def demo_media_pipe(self):
        cap = cv2.VideoCapture(0)
        with Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
            while cap.isOpened():
                ret, frame = cap.read()
                image, results = self.mediapipe_detection(frame, holistic)
                self.draw_styled_landmarks(image, results)
                cv2.imshow('OpenCV Feed', image)
                if cv2.waitKey(10) & 0xFF == ord('q'):
                    break
            cap.release()
            cv2.destroyAllWindows()

    def train_model(self) -> None:
        print("Training model...")
        sequences, labels = self.create_sequences_and_labels('maximize')
        x_arr = np.array(sequences)
        y_arr = to_categorical(labels).astype(int)
        x_train, x_test, y_train, y_test = train_test_split(x_arr, y_arr, test_size=0.05)
        model = Sequential()
        model.add(LSTM(64, return_sequences=True, activation='relu', input_shape=(30, 1662)))
        model.add(LSTM(128, return_sequences=True, activation='relu'))
        model.add(LSTM(64, return_sequences=False, activation='relu'))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(self.actions.shape[0], activation='softmax'))
        model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['categorical_accuracy'])
        model.fit(x_train, y_train, epochs=2000, callbacks=[self._tb_callback])
        model.summary()


if __name__ == '__main__':
    gm: GestureActionManager = GestureActionManager()
    # gm.demo_media_pipe()
    # gm.capture_landmarks('maximize')
    gm.train_model()
