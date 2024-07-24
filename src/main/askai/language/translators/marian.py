from askai.language.ai_translator import AITranslator
from askai.language.language import Language
from functools import lru_cache
from transformers import MarianMTModel, MarianTokenizer


class MarianTranslator(AITranslator):
    """Provides a multilingual offline translation engine.
    """

    # Specify the model name
    MODEL_NAME = 'Helsinki-NLP/opus-mt-en-ROMANCE'

    def __init__(self, from_idiom: Language, to_idiom: Language):
        super().__init__(from_idiom, to_idiom)
        # Load the model and tokenizer
        self._model = MarianMTModel.from_pretrained(self.MODEL_NAME)
        self._tokenizer = MarianTokenizer.from_pretrained(self.MODEL_NAME)

    @lru_cache(maxsize=256)
    def translate(self, text: str) -> str:
        """Translate text using te default translator.
        :param text: Text to translate.
        """
        if self._from_idiom == self._to_idiom:
            return text

        return self._translate(
            f">>{self._to_idiom.idiom}<<{text}",
        )

    def _translate(self, text) -> str:
        """TODO"""
        # Prepare the text for the model
        inputs = self._tokenizer.encode(text, return_tensors="pt", padding=True)
        # Perform the translation
        translated = self._model.generate(inputs)
        # Decode the translated text
        translated_text = self._tokenizer.decode(
            translated[0], skip_special_tokens=True
        )
        return translated_text

    def name(self) -> str:
        return "Marian"


if __name__ == "__main__":
    t = MarianTranslator(Language.EN_US, Language.PT_BR)
    print(t.translate("--- \n Hello \"initialization\"\n How ARE you doing 'what is up'?"))
