#------------------------------
from playwright.async_api import async_playwright
from utils import utils
from concurrent import futures
from file_service import FileService
import re
import asyncio


class InstagramBrowserService(FileService):
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


    def parse_image_post(self, json_data: dict, post_id: str):
        images = []
        caption = ''
        username = json_data['data']['xdt_shortcode_media']['owner']['username']
        for x in json_data['data']['xdt_shortcode_media']['edge_sidecar_to_children']['edges']:
            images.append(x['node']['display_url'])
            caption += f" {x['node']['accessibility_caption']}"
        result = {
            'images': images,
            'caption': caption,
            'post_id': post_id,
            'username': username,
            'type': 'image'
        }
        return result
    

    def parse_video_post(self, json_data: dict, post_id: str):
        video = json_data['data']['xdt_shortcode_media']['video_url']
        caption = json_data['data']['xdt_shortcode_media']['edge_media_to_caption']['edges'][0]['node']['text']
        username = json_data['data']['xdt_shortcode_media']['owner']['username']
        result = {
            'video': video,
            'caption': caption,
            'post_id': post_id,
            'username': username,
            'type': 'video'
        }
        return result
    

    async def load_post(self, url: str, post_id: str):
        async_items = []
        result = None
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=self.headless)
            page = await browser.new_page()
            print('Browser started!')
            page.on('response', lambda response: async_items.append(response.json()) \
            if response.request.url == 'https://www.instagram.com/graphql/query' else None)
            await page.goto(url)
            await page.wait_for_timeout(5000)
            for async_item in async_items:
                try:
                    json_data = await async_item
                    json_data['data']['xdt_shortcode_media']
                    if '/p/' in url:
                        result = self.parse_image_post(json_data, post_id)
                    elif '/reel/' in url:
                        result = self.parse_video_post(json_data, post_id)
                    return result
                except:
                    pass


    def start_tasks(self, result: dict, video_file: str = None, image_folder: str = None) -> dict:
        print('Starting the tasks')
        with futures.ThreadPoolExecutor() as executor:
            if result.get('type') == 'video':
                transcription = executor.submit(utils.transcribe_video, video_file)
                text_detected = executor.submit(utils.extract_frames, video_file)
            elif result.get('type') == 'image':
                transcription = None
                text_detected = executor.submit(utils.convert_image_to_text, image_folder)
        transcription = transcription.result() if transcription else None
        text_detected = text_detected.result()
        item = {
            'post_id': result.get('post_id'),
            'text_detected': text_detected,
            'caption': result.get('caption'),
            'transcript': transcription,
            'username': result.get('username'),
            'social': 'instagram'
        }
        print('Done with the tasks')
        return item


    async def start_service(self):
        if self.post_id:
            post_id = f'instagram_{self.post_id}'
            print('Loading post')
            result = await self.load_post(self.url, post_id)
            print('Done post')
            output = None
            if result.get('type') == 'video':
                output = self.process_video_file(result)
            else:
                output = self.process_image_file(result)
            if output:
                print(f'File service: {output}')
                item = self.start_tasks(result, video_file=output, image_folder=output)
                utils.save_or_append(item)
                return item
        else:
            print('Error with post id')
            return None
    

    def main(self):
        try:
            event_loop = asyncio.new_event_loop()
            item = event_loop.run_until_complete(self.start_service())
        except Exception as e:
            print(f'Error: {e}')
            item = None
        return item


if __name__ == '__main__':
    bs = InstagramBrowserService(url='https://www.instagram.com/instagram/reel/DDz7mgxSadJ/?hl=en')
    item = bs.main()
    print(item)