from pydantic import BaseModel, Field
from typing import Any, List
from enum import Enum

class TextExtraction(BaseModel):
    post_id: Any = None
    text_detected: Any = None
    caption: Any = None
    transcript: Any = None
    social: Any = None

class ResultCategory(Enum):
    restaurant = "Restaurants"
    hotel_accomodations = "Hotels & accommodations"
    bars = "Bars & Nightlife"
    cafe = "Cafés"
    arts = "Arts"
    shopping = "Shopping"
    spas = "Spas"


class ResultMetadata(BaseModel):
    address: str|None = Field(description='Complete address if explicitly mentioned')
    instagram: str|None = Field(description='Instagram handle if mentioned')
    area: str|None = Field(description='Neighborhood or area name if mentioned')


class ResultItem(BaseModel):
    name: str = Field(description='Exact name of the place as mentioned in the content')
    category: ResultCategory = Field(description='Category that best matches the place')
    description: str|None = Field(description='Direct quotes or specific descriptions about this place from the content')
    metadata: ResultMetadata = Field(description='')
    tags: list[str]= Field(description='Key characteristics or features explicitly mentioned about the place')


class ResponseModel(BaseModel):
    title: str = Field(description='A short, descriptive title summarizing the post content', default='')
    contentPlaces: bool = Field(description="Indicates if any places were found in the content", default='')
    city: str|None = Field(description='Main city mentioned in the content, if any', default='')
    results: List[ResultItem] = Field(description='Array of places found in the content. Empty if contentPlaces is false', default=[])