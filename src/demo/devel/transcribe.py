import whisper

FILE = "resources/response_audio.mp3"


if __name__ == '__main__':
    w_model: whisper.Whisper = whisper.load_model("base")

    # Transcribe the audio file. Specify Portuguese language.
    result = whisper.transcribe(model=w_model, audio=FILE, language="pt")

    # Print the transcription result
    print(result["text"])
