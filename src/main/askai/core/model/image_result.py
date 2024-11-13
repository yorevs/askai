from pydantic import BaseModel, Field
from typing import AnyStr


class ImageResult(BaseModel):
    """Information about an image. This class provides a schema for storing and validating image-related information
    using Pydantic's data validation features.
    """

    people_count: int = Field(description="Number of beings on the picture")
    main_objects: list[str] = Field(description="List of the main objects on the picture")
    env_description: str = Field(description="Description of the atmosphere of the environment")
    people_description: list[str] = Field(description="List of people description")
    user_response: list[str] = Field(description="A response to the user question")

    @staticmethod
    def of(image_caption: AnyStr) -> "ImageResult":
        return ImageResult.model_validate_json(str(image_caption).replace("'", '"'))
