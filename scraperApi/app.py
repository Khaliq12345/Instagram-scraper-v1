import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tiktok_service import TiktokBrowserService
from instagram_service import InstagramBrowserService
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Any, Optional, Annotated
from config import config
import social_parser

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

@app.get('/post/text', response_model=social_parser.model.ResponseModel)
def get_post_text(api_key: Annotated[str, Depends(get_api_key)], post_url: str):
    if 'tiktok.com' in post_url:
        browser_service = TiktokBrowserService(post_url)
        result = browser_service.main()
    elif 'www.instagram.com' in post_url:
        browser_service = InstagramBrowserService(post_url)
        result = browser_service.main()
    if result:
        print('Starting the parsing of the output')
        return social_parser.parse_output(result)
    else:
        return social_parser.model.ResponseModel()

# if __name__ == '__main__':
#     Path('outputs').mkdir(exist_ok=True)
#     result = tiktok_service.main('https://www.tiktok.com/@micro2rouen/video/7444916723704171798?is_from_webapp=1')
#     print(result)