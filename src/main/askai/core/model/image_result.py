from pydantic import BaseModel, Field
from typing import AnyStr, Optional

import ast
import json


class ImageResult(BaseModel):
    """Information about an image. This class provides a schema for storing and validating image-related information
    using Pydantic's data validation features.
    """

    people_count: Optional[int] = Field(description="Number of beings on the picture", default=None, ge=0)
    main_objects: list[str] = Field(description="List of the main objects on the picture", default=None)
    env_description: str = Field(description="Description of the atmosphere of the environment")
    people_description: list[str] = Field(description="List of people description", default=None)
    user_response: Optional[str] = Field(description="A response to the user question", default=None)

    @staticmethod
    def of(image_caption: AnyStr) -> "ImageResult":
        """Parses a string into an ImageResult instance with enhanced handling for mixed quotes.
        :param image_caption: The string to parse.
        :return: An instance of ImageResult populated with the parsed data.
        :raises ValueError: If the string cannot be parsed as a Python object or JSON.
        """

        try:
            parsed_data = ast.literal_eval(image_caption)
        except (ValueError, SyntaxError):
            try:
                parsed_data = json.loads(image_caption)
            except json.JSONDecodeError as e_json:
                raise ValueError("String could not be parsed as Python object or JSON.") from e_json
        try:
            return ImageResult(**parsed_data)
        except Exception as e_pydantic:
            raise ValueError("Parsed data does not conform to ImageResult schema.") from e_pydantic
