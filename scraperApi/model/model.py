from pydantic import BaseModel
from typing import Any

class TextExtraction(BaseModel):
    post_id: Any = None
    text_detected: Any = None
    caption: Any = None
    transcript: Any = None
    social: Any = None