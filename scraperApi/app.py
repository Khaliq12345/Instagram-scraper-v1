import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tiktok import tiktok_service
from instagram import instagram_service
from fastapi import FastAPI
from pydantic import BaseModel

class TextExtraction(BaseModel):
    post_id: str|None = None
    text_detected: str|None = None
    caption: str|None = None
    transcript: str|None = None
    social: str|None = None


app = FastAPI()

@app.get('/post/text', response_model=TextExtraction)
def get_post_text(post_url: str, social: str):
    if social == 'tiktok':
        result = tiktok_service.main(post_url)
    elif social == 'instagram':
        result = instagram_service.main(post_url)
    if result:
        return result
    else:
        return TextExtraction()

# if __name__ == '__main__':
#     Path('outputs').mkdir(exist_ok=True)
#     result = tiktok_service.main('https://www.tiktok.com/@micro2rouen/video/7444916723704171798?is_from_webapp=1')
#     print(result)