from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Page
from utils import utils
from concurrent import futures
import asyncio
from file_service import FileService
from selectolax.parser import HTMLParser
import re
import os
from pathlib import Path
import httpx


class TiktokBrowserService(FileService):
    def __init__(self, url):
        super().__init__()
        self.headless = False
        self.url = url
        self.proxy= {
            'server': 'us.smartproxy.com:10000',
            'username': utils.PROXY_USERNAME,
            'password': utils.PROXY_PASSWORD
        }


    def extract_tiktok_id(self, url):
        if '//vm.' in url:
            response = httpx.get(
                url,
                timeout=None,
                follow_redirects=True
            )
            url = str(response.url)
        pattern = r'https?://(?:www\.)?tiktok\.com/@([^/]+)/(?:video|photo)/(\d+)(?:\?.*)?'
        match = re.match(pattern, url)
        if match:
            pid = match.group(2)
            return pid
        else:
            return {}


    def process_video_file(self, result):
        video = result.get('video_body')
        post_id = result.get('post_id')
        folder = os.path.join(self.video_folder, post_id)
        Path(folder).mkdir(exist_ok=True)
        file_name = f'{folder}/video.mp4'
        with open(file_name, 'wb') as file:
            chunk_size = 8192
            for i in range(0, len(video), chunk_size):
                file.write(video[i:i + chunk_size])
        return file_name


    async def load_post(self, url: str, post_id: str):
        result = None
        try:
            browser = await AsyncCamoufox(headless=self.headless).start()
            page: Page = await browser.new_page(proxy=self.proxy)
            print('Browser started!')
            await page.goto(url)
            await page.wait_for_timeout(5000)
            if await page.is_visible('button[id="captcha_close_button"]'):
                await page.click('button[id="captcha_close_button"]')
            html = await page.content()
            soup = HTMLParser(html)
            video_url = soup.css_first('video source').attributes['src']
            await page.goto(video_url)
            response = await page.request.get(video_url)
            body = await response.body()
            caption = soup.css_first('h1[data-e2e="browse-video-desc"]').text()
            result = {
                'video_body': body,
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
    

    async def start_service(self):
        post_id = self.extract_tiktok_id(self.url)
        if post_id:
            post_id = f'tiktok_{post_id}'
            is_exists = utils.is_exists(post_id)
            if is_exists:
                return is_exists
            print('Loading post')
            result = await self.load_post(self.url, post_id)
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
            item = asyncio.run(self.start_service())
        except Exception as e:
            print(f'Error: {e}')
            item = None
        return item


if __name__ == '__main__':
    bs = TiktokBrowserService(
        url='https://www.tiktok.com/@elomaxmax_tv/video/7438498380797480225'
    )
    item = bs.main()
    print(item)
