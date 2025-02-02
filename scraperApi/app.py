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
from place_service import get_place_info

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
    places = []
    print('Starting the parsing of the output')
    if result:
        is_exists = utils.is_exists('post_id', result.get('post_id'), 'posts')
        if is_exists:
            post = Post(**is_exists)
            mentions = utils.is_exists('post_id', result.get('post_id'), 'mentions', is_single=False)
            for mention in mentions:
                query = mention.get('place_name')
                if query:
                    query = f"{query} {mention.get('address')}" if mention.get('address') else query
                    place = get_place_info(query)
                    places.append(place)
            return places
        else:
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
                query = result_json.get('place_name')
                if query:
                    query = f"{query} {result_json.get('address')}" if result_json.get('address') else query
                    place = get_place_info(query)
                    result_json['place_id'] = place.get('place_id')
                    places.append(place)
                    mentions.append(result_json)
            utils.save_or_append(mentions, table='mentions')
        return places
    else:
        return []

@app.get('/post/text')
def get_post_text(api_key: Annotated[str, Depends(get_api_key)], post_url: str):
    result = None
    if 'tiktok.com' in post_url:
        post_id = utils.extract_tiktok_id(post_url)
        is_exists = utils.is_exists('post_id', f'tiktok_{post_id}', 'post_creator_view')
        if is_exists:
            result = is_exists
        else:
            browser_service = TiktokBrowserService(post_url, post_id)
            result = browser_service.main()
    elif 'www.instagram.com' in post_url:
        post_id = utils.extract_instagram_id(post_url)
        is_exists = utils.is_exists('post_id', f'instagram_{post_id}', 'post_creator_view')
        if is_exists:
            result = is_exists
        else:
            browser_service = InstagramBrowserService(post_url, post_id)
            result = browser_service.main()
    else:
        return []
    return parse_result(result)

if __name__ == '__main__':
    # browser_service = TiktokBrowserService('https://www.tiktok.com/@onijekujelagos/video/7395894585387420934?q=restaurant&t=1735029668161', '7395894585387420934')
    # result = browser_service.main()
    # print(result)
    # Path('outputs').mkdir(exist_ok=True)
    # result = tiktok_service.main('https://www.tiktok.com/@micro2rouen/video/7444916723704171798?is_from_webapp=1')
    # print(result)
    uvicorn.run(app, host="0.0.0.0", port=5000)

