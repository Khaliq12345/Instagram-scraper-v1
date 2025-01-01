import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tiktok import tiktok_service
from instagram import instagram_service
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any

class TextExtraction(BaseModel):
    post_id: Any = None
    text_detected: Any = None
    caption: Any = None
    transcript: Any = None
    social: Any = None


app = FastAPI()

@app.get('/post/text', response_model=TextExtraction)
def get_post_text(post_url: str):
    if 'www.tiktok.com' in post_url:
        result = tiktok_service.main(post_url)
    elif 'www.instagram.com' in post_url:
        result = instagram_service.main(post_url)
    if result:
        return result
    else:
        return TextExtraction()

# if __name__ == '__main__':
#     Path('outputs').mkdir(exist_ok=True)
#     result = tiktok_service.main('https://www.tiktok.com/@micro2rouen/video/7444916723704171798?is_from_webapp=1')
#     print(result)