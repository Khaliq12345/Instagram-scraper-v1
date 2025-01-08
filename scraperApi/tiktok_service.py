from playwright.async_api import async_playwright
from utils import utils
from concurrent import futures
import asyncio
from file_service import FileService
from selectolax.parser import HTMLParser
import re
import os
from pathlib import Path
import httpx
import shutil
import pyktok as pyk
pyk.specify_browser('firefox')


class TiktokBrowserService(FileService):
    def __init__(self, url, post_id):
        super().__init__()
        self.headless = True
        self.url = url
        self.post_id = post_id
        self.proxy= {
            'server': 'us.smartproxy.com:10000',
            'username': utils.PROXY_USERNAME,
            'password': utils.PROXY_PASSWORD
        }

    def process_video_file(self, result):
        video_path = result.get('video_path')
        post_id = result.get('post_id')
        folder = os.path.join(self.video_folder, post_id)
        Path(folder).mkdir(exist_ok=True)
        file_name = f'{folder}/video.mp4'
        shutil.move(video_path, file_name)
        return file_name


    def load_post(self, url: str, post_id: str):
        result = None
        try:
            json_data = pyk.alt_get_tiktok_json(url)
            try:
                caption = json_data['__DEFAULT_SCOPE__']['webapp.video-detail']['itemInfo']['itemStruct']['desc']
            except:
                caption = None
            json_data = pyk.save_tiktok(
                video_url=url,
                save_video=True,
                metadata_fn='',
                return_fns=True
            )
            result = {
                'video_path': json_data['video_fn'],
                'caption': caption,
                'post_id': post_id,
                'type': 'video'
            }
            return result
        except Exception as e:
            print(f'Error: {str(e)}')
            return result
        

    def start_tasks(self, result: dict, video_file: str = None) -> dict:
        print('Starting the tasks')
        with futures.ThreadPoolExecutor() as executor:
            transcription = executor.submit(utils.transcribe_video, video_file)
            text_detected = executor.submit(utils.extract_frames, video_file)
        transcription = transcription.result() if transcription else None
        text_detected = text_detected.result()
        item = {
            'post_id': result.get('post_id'),
            'text_detected': text_detected,
            'caption': result.get('caption'),
            'transcript': transcription,
            'social': 'tiktok'
        }
        print('Done with the tasks')
        return item
    

    def start_service(self):
        if self.post_id:
            print('Loading post')
            result = self.load_post(self.url, f'tiktok_{self.post_id}')
            print('Done post')
            output = None
            output = self.process_video_file(result)
            if output:
                print(f'File service: {output}')
                item = self.start_tasks(result, video_file=output)
                utils.save_or_append(item)
                return item
        else:
            print('Error with post id')
            return None
        

    def main(self):
        try:
            item = self.start_service()
        except Exception as e:
            print(f'Error: {e}')
            item = None
        return item


if __name__ == '__main__':
    bs = TiktokBrowserService(
        url='https://www.tiktok.com/@onijekujelagos/video/7395894585387420934?q=restaurant&t=1735029668161'
    )
    item = bs.main()
    print(item)
