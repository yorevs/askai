from askai.core.router.evaluation import resolve_x_refs
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text
from utils import get_resource, init_context

# if __name__ == "__main__":
#     queries_files: list[str] = [
#         "Open 1",
#         "Open second",
#         "Open 3",
#         "Open <AC/DC_Song>",
#         "Open it",
#         "Open any",
#         "Open the most recent",
#         "Open the most oldest",
#         "open metalica",
#     ]
#     init_context("x_refs_demo")
#     ctx: str = get_resource("songs")
#     display_text(f"\n```bash\n{ctx}\n```\n")
#     # Provide the context
#     shared.context.push("HISTORY", ctx)
#     shared.context.push("HISTORY", "Is there any song about cars?")
#     shared.context.push("HISTORY", 'Yes, there is. The song is "Highway to Hell"', "assistant")
#     for query in queries_files:
#         print(f"({shared.context.size('HISTORY')}/{shared.context.max_context_size})", "QUESTION: ", query)
#         resp: str = resolve_x_refs(query)
#         display_text(f"Response: {resp}")

from tokenizers.decoders import DecodeStream
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained('meta-llama/Meta-Llama-3-8B-Instruct')
stream = DecodeStream(skip_special_tokens=False)

prompt = "To modify below `HTML` to `{{ '{KEY}' | transalte }}` obeys below Keys.\nExample:\n{{ 'Text.Action\\_Edit' | transalte }}\nKeys:\nText.Action\\_Edit\nText.Action\\_Log\nText.Action\\_View\nText.Action\\_Clone\nText.Action\\_Credit\nText.Action\\_CancelReward\nHTML:\n \n [View](#)\n[Edit](17.reward-template-setting.html)\n[Clone](#)\n[Credit](#)\n[Cancel Rewards](#)\n[Log](#)"

token_ids = tok(prompt).input_ids
# [1271, 5719, 3770, 1595, 5959, 63, 311, 1595, 3052, 11834, 4889, 11923, 765, 1380, 93420, 3954, 63, 98502, 1065, 3770, 25104, 627, 13617, 512, 3052, 364, 1199, 11614, 76838, 4126, 6, 765, 1380, 93420, 8256, 9026, 512, 1199, 11614, 76838, 4126, 198, 1199, 11614, 76838, 2250, 198, 1199, 11614, 76838, 860, 198, 1199, 11614, 76838, 38777, 198, 1199, 11614, 76838, 34593, 198, 1199, 11614, 76838, 9453, 60722, 198, 5959, 512, 720, 510, 860, 9725, 2, 340, 58, 4126, 9725, 1114, 83480, 34509, 61556, 2628, 340, 58, 38777, 9725, 2, 340, 58, 34593, 9725, 2, 340, 58, 9453, 50868, 9725, 2, 340, 58, 2250, 9725, 2, 8]

for token_id in token_ids:
   stream.step(tok._tokenizer, token_id)
