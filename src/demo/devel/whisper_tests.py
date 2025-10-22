from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_MAP = {
    "chat": {
        "include": ["gpt-", "o1", "o3", "o4", "chatgpt"],
        "exclude": ["tts", "whisper", "embedding", "dall", "image", "sora", "moderation", "audio", "transcribe"],
    },
    "audio": {
        "include": ["tts", "whisper", "audio", "realtime", "transcribe"],
        "exclude": [],
    },
    "image": {
        "include": ["dall-e", "image", "sora"],
        "exclude": [],
    },
    "embedding": {
        "include": ["embedding", "ada"],
        "exclude": [],
    },
    "moderation": {
        "include": ["moderation"],
        "exclude": [],
    },
    "code": {
        "include": ["codex", "gpt-5-codex"],
        "exclude": [],
    },
    "video": {
        "include": ["sora"],
        "exclude": [],
    },
}


def models(model_type: str = "chat") -> None:
    """List models by category (chat, audio, image, etc.)."""
    if model_type not in MODEL_MAP:
        print(f"Unknown type: {model_type}")
        return

    cfg = MODEL_MAP[model_type]
    all_models = client.models.list()

    filtered = [
        m.id for m in all_models.data
        if any(k in m.id for k in cfg["include"])
        and not any(x in m.id for x in cfg["exclude"])
    ]

    for model_id in sorted(set(filtered)):
        print(model_id)


def voices():
    all_voices = [
        'alloy', 'echo', 'fable', 'onyx',
        'nova', 'shimmer', 'coral', 'verse',
        'ballad', 'ash', 'sage', 'marin', 'cedar'
    ]
    name_or_index = 12
    voice_name = name_or_index if isinstance(name_or_index, str) else all_voices[int(name_or_index)]

    speech = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice_name,
        input="How can I assist you today?"
    )

    with open(f"resources/openai-{voice_name}-sample.mp3", "wb") as f:
        f.write(speech.read())


if __name__ == '__main__':
    models("image")
