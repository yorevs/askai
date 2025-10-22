#!/usr/bin/env python3
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def chat_demo(prompt: str | None):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt or "Explain quantum computing in one sentence."}],
    )
    print("Chat:", resp.choices[0].message.content)


def code_demo(prompt: str | None):
    resp = client.chat.completions.create(
        model="gpt-5-codex",
        messages=[{"role": "user", "content": prompt or "Write a Python function to reverse a string."}],
    )
    print("Code:", resp.choices[0].message.content)


def voice_demo(prompt: str | None):
    voice = "alloy"
    speech = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=prompt or "How can I assist you today?"
    )
    os.makedirs("resources", exist_ok=True)
    out = f"resources/{voice}.mp3"
    with open(out, "wb") as f:
        f.write(speech.read())
    print(f"Voice sample saved: {out}")


def transcribe_demo(filename: str = "response_audio.mp3"):
    print(f"Transcribing {filename} ...")
    with open(filename, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    print("Transcript:", transcript.text)


def image_demo(prompt: str | None):
    resp = client.images.generate(
        model="dall-e-3",
        prompt=prompt or "A futuristic robot head, blue and with engines, digital art",
        size="1024x1024"
    )
    url = resp.data[0].url
    print("Image URL:", url)


def embedding_demo(prompt: str | None):
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=prompt or "The quick brown fox jumps over the lazy dog"
    )
    print("Embedding length:", len(resp.data[0].embedding))


def moderation_demo(prompt: str | None):
    resp = client.moderations.create(
        model="omni-moderation-latest",
        input=prompt or "I want to harm someone"
    )
    print("Flagged:", resp.results[0].flagged)


def search_demo(prompt: str | None):
    resp = client.chat.completions.create(
        model="gpt-5-search-api",
        messages=[{"role": "user", "content": prompt or "Find the latest Mars exploration news."}]
    )
    print("Search:", resp.choices[0].message.content)


def video_demo(prompt: str | None):
    resp = client.images.generate(
        model="sora",
        prompt=prompt or "A drone flying over a tropical island beach at sunrise"
    )
    print("Video (simulated output URL):", resp.data[0].url)


def menu():
    actions = {
        "1": ("Chat / Reasoning", chat_demo),
        "2": ("Code", code_demo),
        "3": ("Voice / TTS", voice_demo),
        "4": ("Speech-to-Text", transcribe_demo),
        "5": ("Vision / Image", image_demo),
        "6": ("Video / Animation", video_demo),
        "7": ("Embedding / Vector", embedding_demo),
        "8": ("Moderation / Safety", moderation_demo),
        "9": ("Search / Retrieval", search_demo),
        "0": ("Exit", None),
    }

    while True:
        print("\n=== OpenAI Model Type Demo ===")
        for k, (name, _) in actions.items():
            print(f"[{k}] {name}")
        choice = input("Select an option: ").strip()
        if choice == "0":
            break
        if choice in actions:
            print(f"\nRunning: {actions[choice][0]}...\n")
            try:
                prompt = input("Prompt: ")
                actions[choice][1](prompt)
            except Exception as e:
                print("Error:", e)
        else:
            print("Invalid option.")


if __name__ == "__main__":
    menu()
