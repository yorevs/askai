import os
import requests

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")


def get_available_voices():
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        voices = response.json().get("voices", [])
        for voice in sorted(voices, key=lambda v: v["name"]):
            print(f"Name: {voice['name']}, ID: {voice['voice_id']}")
    else:
        print(f"Failed to retrieve voices: {response.status_code}, {response.text}")


if __name__ == "__main__":
    get_available_voices()
