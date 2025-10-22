from askai.language.language import Language
from askai.language.translators.argos_translator import ArgosTranslator
from askai.language.translators.deepl_translator import DeepLTranslator
from askai.language.translators.marian_translator import MarianTranslator
from hspylib.core.tools.commons import sysout

if __name__ == "__main__":
    text = """
    This is just a 'Translator' test. there are some **Markdown Formatted**
    1. Bullet 1
    2. Bullet 2
    "This should not be translated"
    'This should not be translated'
    ∆ Finished.
    """
    from_lang: Language = Language.EN_US
    to_lang: Language = Language.PT_BR

    match tt := input("\n1. DeepL\n2. Marian\n3. Argos-Translate\nChoose Translator [Argos-Translate]: "):
        case '1':
            # DeepL
            t = DeepLTranslator(from_lang, to_lang)
            sysout("DeepL: ", t.translate(text))
        case '2':
            # Marian
            m = MarianTranslator(from_lang, to_lang)
            sysout("Marian: ", m.translate(text))
        case _:
            # Argos-Translate
            a = ArgosTranslator(from_lang, to_lang)
            sysout("Argos: ", a.translate(text))
