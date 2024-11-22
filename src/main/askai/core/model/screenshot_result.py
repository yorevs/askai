import ast
import json
from typing import AnyStr

from kubernetes.watch.watch import SimpleNamespace
from pydantic import BaseModel, Field


class ScreenshotResult(BaseModel):
    """Information about an image. This class provides a schema for storing and validating image-related information
    using Pydantic's data validation features.
    """

    class DocumentModel(BaseModel):
        """TODO"""

        page_number: int = Field(description="Document page number")
        header: str = Field(description="Document header content")
        footer: str = Field(description="Document footer content")
        content_overview: str = Field(description="Document content overview")

    class WebsiteModel(BaseModel):
        """TODO"""

        website_description: str = Field(description="Website description")
        website_url: str = Field(description="Website URL")

    open_applications: list[str] = Field(description="List of open applications")
    open_documents: list[DocumentModel] = Field(description="List of document descriptions")
    web_pages: list[WebsiteModel] = Field(description="Description of visible web pages")
    user_response: str = Field(description="A response to the user question")

    @staticmethod
    def of(image_caption: AnyStr) -> "ScreenshotResult":
        """Parses a string into an ScreenshotResult instance with enhanced handling for mixed quotes.
        :param image_caption: The string to parse.
        :return: An instance of ScreenshotResult populated with the parsed data.
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
            return ScreenshotResult(**parsed_data)
        except Exception as e_pydantic:
            raise ValueError("Parsed data does not conform to ScreenshotResult schema.") from e_pydantic
