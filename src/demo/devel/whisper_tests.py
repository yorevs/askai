from openai import OpenAI

client = OpenAI()

voices = [
    'alloy', 'echo', 'fable', 'onyx',
    'nova', 'shimmer', 'coral', 'verse',
    'ballad', 'ash', 'sage', 'marin', 'cedar'
]
name_or_index = 12
voice_name = name_or_index if isinstance(name_or_index, str) else voices[int(name_or_index)]

speech = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice=voice_name,
    input="How can I assist you today?"
)

with open(f"resources/openai-{voice_name}-sample.mp3", "wb") as f:
    f.write(speech.read())
