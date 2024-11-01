from transformers import GPT2LMHeadModel, GPT2Tokenizer
from typing import AnyStr

import os.path
import torch


def initialize(model_name: str = "gpt2") -> tuple:
    """Initializes the specified GPT-2 model and its tokenizer. Downloads them if not already cached. Choose a model
    size. 'gpt2' is the smallest; larger models like 'gpt2-medium', 'gpt2-large'
    :param model_name: The name of the model to initialize (default is 'gpt2').
    :return: A tuple containing the model and the tokenizer.
    """

    if not os.path.exists(f"./{model_name}_tokenizer") or not os.path.exists(f"./{model_name}_model"):

        # Download and cache the tokenizer and model
        tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        model = GPT2LMHeadModel.from_pretrained(model_name)

        # Save them locally for offline use
        tokenizer.save_pretrained(f"./{model_name}_tokenizer")
        model.save_pretrained(f"./{model_name}_model")

    # Load the tokenizer and model from local directories
    tokenizer = GPT2Tokenizer.from_pretrained(f"./{model_name}_tokenizer")
    model = GPT2LMHeadModel.from_pretrained(f"./{model_name}_model")

    # Set the model to evaluation mode
    model.eval()

    return model, tokenizer


def predict_next_word(text: AnyStr, num_words: int = 2, top_k: int = 5) -> list[str]:
    """Predict multiple next words by iteratively feeding generated words back into the model.
    :param text: The input text.
    :param num_words: Number of words to predict.
    :param top_k: Number of top predictions to consider at each step.
    :return: The input text appended with the predicted words.
    """

    model, tokenizer = initialize()

    # Encode the input text into token IDs
    input_ids = tokenizer.encode(text, return_tensors="pt")

    # Disable gradient calculations for efficiency
    with torch.no_grad():
        # Get model outputs (logits)
        outputs = model(input_ids)
        logits = outputs.logits

    # Focus on the logits of the last token in the input
    next_token_logits = logits[0, -1, :]

    # Retrieve the top_k token IDs with the highest logits
    top_k_logits, top_k_indices = torch.topk(next_token_logits, top_k)

    # Decode the token IDs to actual words/strings
    predicted_words: list[str] = [tokenizer.decode([idx]).strip() for idx in top_k_indices.tolist()]
    predicted_words.sort(key=len, reverse=True)

    return predicted_words


if __name__ == "__main__":
    while (query := input("$ ")) and query not in ["e", "q"]:
        result = predict_next_word(query)
        print(result)
