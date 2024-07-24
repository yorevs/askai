import deepl
import os

if __name__ == '__main__':
    auth_key = os.environ.get("DEEPL_API_KEY")
    translator = deepl.Translator(auth_key)

    result = translator.translate_text(
        "Hello, world! 'Introduction'",
        preserve_formatting=True,
        source_lang="EN", target_lang="FR"
    )
    print(result.text)  # "Bonjour, le monde !"
