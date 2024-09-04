from typing import Any

from pydantic import BaseModel, Field


class ImageResult(BaseModel):
    """Information about an image. This class provides a schema for storing and validating image-related information
    using Pydantic's data validation features.
    """
    people_count: int = Field(description="Number of beings on the picture")
    main_objects: list[str] = Field(description="List of the main objects on the picture")
    env_description: str = Field(description="Description of the atmosphere of the environment")
    people_description: list[str] = Field(description="List of people description")

    @staticmethod
    def to_image_result(from_dict: dict[str, Any]) -> 'ImageResult':
        return ImageResult.MyModel.parse_obj(
            from_dict['people_count'],
            from_dict['main_objects'],
            from_dict['env_description'],
            from_dict['people_description'])
