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
from utils import utils
import json
import uvicorn
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME)
Instrumentator().instrument(app).expose(app)

def get_api_key(
    api_key: Optional[str] = Depends(api_key_header)
):
    if api_key != config.APP_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )
    return api_key


def supabase_checker(post_id: str, social: str):
    is_exists = utils.is_exists(f'{social}_{post_id}')
    if is_exists:
        is_parsed = utils.is_exists(f'{social}_{post_id}', 'parse_output')
        if is_parsed:
            is_parsed['results'] = [json.loads(item) for item in is_parsed['results']]
            return is_parsed
        return social_parser.parse_output(is_exists)


@app.get('/post/text', response_model=social_parser.model.ResponseModel)
def get_post_text(api_key: Annotated[str, Depends(get_api_key)], post_url: str):
    result = None
    if 'tiktok.com' in post_url:
        post_id = utils.extract_tiktok_id(post_url)
        output = supabase_checker(post_id, 'tiktok')
        if output:
            return output
        browser_service = TiktokBrowserService(post_url, post_id)
        result = browser_service.main()
    elif 'www.instagram.com' in post_url:
        post_id = utils.extract_instagram_id(post_url)
        output = supabase_checker(post_id, 'instagram')
        if output:
            return output
        browser_service = InstagramBrowserService(post_url, post_id)
        result = browser_service.main()
    else:
        return social_parser.model.ResponseModel()
    if result:
        print('Starting the parsing of the output')
        return social_parser.parse_output(result)
    else:
        return social_parser.model.ResponseModel()

if __name__ == '__main__':
    # Path('outputs').mkdir(exist_ok=True)
    # result = tiktok_service.main('https://www.tiktok.com/@micro2rouen/video/7444916723704171798?is_from_webapp=1')
    # print(result)
    uvicorn.run(app, host="0.0.0.0", port=5000)