import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tiktok_service import TiktokBrowserService
from instagram_service import InstagramBrowserService
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import APIKeyHeader
from typing import Any, Optional, Annotated
from config import config
import social_parser
from model.model import Post, ResponseModel
from utils import utils
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

def parse_result(result: dict):
    if result:
        print('Starting the parsing of the output')
        response: ResponseModel = social_parser.parse_output(result)
        post = Post(
            post_id=result.get('post_id'),
            text_detected=result.get('text_detected'),
            caption=result.get('caption'),
            transcript=result.get('transcript'),
            social=result.get('social'),
            city=response.city,
            title=response.title,
            creator_id=result.get('username'),
            content_places=response.contentPlaces
        )
        utils.save_or_append({'username': post.creator_id}, table='creators')
        utils.save_or_append(jsonable_encoder(post), table='posts')
        mentions = []
        for result in response.results:
            result_json = jsonable_encoder(result)
            result_json['post_id'] = post.post_id
            mentions.append(result_json)
        utils.save_or_append(mentions, table='mentions')
        return post
    else:
        return Post()


@app.get('/post/text', response_model=Post)
def get_post_text(api_key: Annotated[str, Depends(get_api_key)], post_url: str):
    result = None
    if 'tiktok.com' in post_url:
        post_id = utils.extract_tiktok_id(post_url)
        is_exists = utils.is_exists(f'tiktok_{post_id}', 'posts')
        if is_exists:
            return Post(**is_exists)
        browser_service = TiktokBrowserService(post_url, post_id)
        result = browser_service.main()
    elif 'www.instagram.com' in post_url:
        post_id = utils.extract_instagram_id(post_url)
        is_exists = utils.is_exists(f'instagram_{post_id}', 'posts')
        if is_exists:
            return Post(**is_exists)
        browser_service = InstagramBrowserService(post_url, post_id)
        result = browser_service.main()
    else:
        return Post()
    return parse_result(result)

if __name__ == '__main__':
    # browser_service = TiktokBrowserService('https://www.tiktok.com/@onijekujelagos/video/7395894585387420934?q=restaurant&t=1735029668161', '7395894585387420934')
    # result = browser_service.main()
    # print(result)
    # Path('outputs').mkdir(exist_ok=True)
    # result = tiktok_service.main('https://www.tiktok.com/@micro2rouen/video/7444916723704171798?is_from_webapp=1')
    # print(result)
    uvicorn.run(app, host="0.0.0.0", port=5500)