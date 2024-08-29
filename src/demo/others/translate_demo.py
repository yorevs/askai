from transformers import MarianMTModel, MarianTokenizer

if __name__ == "__main__":

    # Specify the model name
    model_name = "Helsinki-NLP/opus-mt-en-ROMANCE"

    # Load the model and tokenizer
    model = MarianMTModel.from_pretrained(model_name)
    tokenizer = MarianTokenizer.from_pretrained(model_name)

    # Function to translate text
    def translate(text, model, tokenizer):
        # Prepare the text for the model
        inputs = tokenizer.encode(text, return_tensors="pt", padding=True)
        # Perform the translation
        translated = model.generate(inputs)
        # Decode the translated text
        translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
        return translated_text

    # Example text to translate
    text_to_translate = ">>es_ES<< Hello, how are you?"

    # Perform the translation
    translated_text = translate(text_to_translate, model, tokenizer)
    print(translated_text)
