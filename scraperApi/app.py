import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tiktok import tiktok_service
from instagram import instagram_service
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Any, Optional, Annotated
from config import config
from model.model import TextExtraction

app = FastAPI()
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME)

def get_api_key(
    api_key: Optional[str] = Depends(api_key_header)
):
    if api_key != config.APP_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )
    return api_key

@app.get('/post/text', response_model=TextExtraction)
def get_post_text(api_key: Annotated[str, Depends(get_api_key)], post_url: str):
    if 'tiktok.com' in post_url:
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