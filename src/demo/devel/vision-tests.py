import base64

from langchain.chains.transform import TransformChain
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import chain
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from pydantic.v1 import Field


def load_image(inputs: dict) -> dict:
    """Load image from file and encode it as base64."""
    image_path = inputs["image_path"]

    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    image_base64 = encode_image(image_path)
    return {"image": image_base64}


class ImageInformation(BaseModel):
    """Information about an image."""
    image_description: str = Field(description="a short description of the image")
    people_count: int = Field(description="number of humans on the picture")
    main_objects: list[str] = Field(description="list of the main objects on the picture")


load_image_chain = TransformChain(
    input_variables=["image_path", "parser_guides"],
    output_variables=["image"],
    transform=load_image
)

# Set verbose
parser = JsonOutputParser(pydantic_object=ImageInformation)


def get_image_informations(image_path: str) -> dict:
    vision_prompt = """
    Given the image, provide the following information:
    - A count of how many people are in the image
    - A list of the main objects present in the image
    - A description of the image
    """
    vision_chain = load_image_chain | image_model | parser
    return vision_chain.invoke(
        {
            'image_path': f'{image_path}',
            "parser_guides": parser.get_format_instructions(),
            'prompt': vision_prompt
        })


@chain
def image_model(inputs: dict) -> str | list[str] | dict:
    """Invoke model with image and prompt."""
    model = ChatOpenAI(temperature=0.5, model="gpt-4o-mini", max_tokens=1024)
    msg = model.invoke(
        [HumanMessage(
            content=[
                {"type": "text", "text": inputs["prompt"]},
                {"type": "text", "text": parser.get_format_instructions()},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{inputs['image']}"}},
            ])]
    )
    return msg.content


if __name__ == '__main__':
    result = get_image_informations("/Users/hjunior/Library/CloudStorage/Dropbox/Media/eu-edvaldo-suecia.jpg")
    print(result)
