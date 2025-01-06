import os

import speech_recognition as sr
import requests

# Replace these with your actual API keys
from askai.core.component.audio_player import player

# -------------------- Configuration --------------------

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

# ElevenLabs Voice ID (obtained from the previous step)
VOICE_ID = "7fbQ7yJuEo56rYjrYaEh"

# Path to save the synthesized audio
AUDIO_OUTPUT_PATH = "response_audio.mp3"


def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=0.2)
        print("Listening... Please speak into the microphone.")
        audio = recognizer.listen(source)
    try:
        # Using Google Speech Recognition
        text = recognizer.recognize_google(audio)
        print(f"Recognized Text: {text}")
        return text
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio.")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
    return None


def synthesize_speech(text):
    print("Synthesizing speech with ElevenLabs...")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

    headers = {
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY,
    }

    data = {"text": text, "voice_settings": {"stability": 0.75, "similarity_boost": 0.75}}

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        with open(AUDIO_OUTPUT_PATH, "wb") as f:
            f.write(response.content)
        print(f"Audio synthesized and saved as {AUDIO_OUTPUT_PATH}")
        player.play_audio_file(AUDIO_OUTPUT_PATH)
    else:
        print(f"Failed to synthesize speech: {response.status_code}, {response.text}")


def main():
    input_text = recognize_speech()
    if input_text:
        synthesize_speech(input_text)


if __name__ == "__main__":
    main()
