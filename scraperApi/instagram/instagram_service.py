import sys
import os
from pathlib import Path
sys.path.append(Path(os.getcwd()).parent.as_posix())
#-------------------------
from instaloader import Instaloader, Post
import os
from utils import utils
from pathlib import Path
import shutil
from concurrent.futures import ThreadPoolExecutor
from config import config
from openai import OpenAI
import re

# username = 'sp0353n6xj'
# password = 'nh7M8jeqmT4S3sqE~o'
# os.environ['https_proxy'] = f"http://{username}:{password}@gate.smartproxy.com:10001"

# username = 'sp0353n6xj'
# #http://sp0353n6xj:nh7M8jeqmT4S3sqE~o@gate.smartproxy.com:10001

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = Path(CURRENT_DIR).parent.as_posix()
OUTPUT_FILE = os.path.join(PARENT_DIR, 'outputs/outputs.csv')

def get_short_code(post_url: str) -> str|None:
    pattern = r'/(?:reel|p)/([a-zA-Z0-9_-]+)'
    match = re.search(pattern, post_url)
    if match:
        return match.group(1)
    else:
        return None


def instagram_transcript(POST_FOLDER: str) -> str|None:
    files = os.listdir(POST_FOLDER)
    print(f'Starting Transcription')
    for file in files:
        file_path = os.path.join(POST_FOLDER, file)
        if file_path.endswith('.mp4'):
            try:
                client = OpenAI(
                    api_key=config.OPENAI_API_KEY
                )
                audio_file= open(file_path, "rb")
                transcription = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
                return transcription.text
            except Exception as e:
                print(f'Error: {e}')
                return None
            finally:
                print(f'Transcription Done')
    return None
    

def video_to_text(POST_FOLDER: str, post_name: str):
    print('Started Video text extraction')
    files = os.listdir(POST_FOLDER)
    final_text = ''
    for file in files:
        file_path = os.path.join(POST_FOLDER, file)
        if file_path.endswith('.mp4'):
            video_frame_folder = utils.extract_frames(file_path, post_name)
            text = utils.convert_image_to_text(video_frame_folder)
            final_text += f' {text}'
            break
    print('Done Video text extraction')
    return final_text


def image_to_text(POST_FOLDER_IMAGES: str):
    print('Started Image text extraction')
    text = utils.convert_image_to_text(POST_FOLDER_IMAGES)
    print('Done Image text extraction')
    return text


def start_the_tasks(post_id: str, post_name: str, caption: str, post_folder: str,  post_folder_image: str):
    with ThreadPoolExecutor() as executor:
        video_text_detected = executor.submit(video_to_text, post_folder, post_name)
        image_text_detected = executor.submit(image_to_text, post_folder_image)
        transcript = executor.submit(instagram_transcript, post_folder)
    video_text_detected = video_text_detected.result()
    image_text_detected = image_text_detected.result()
    text_detected = f'{video_text_detected} {image_text_detected}'
    transcript = transcript.result()
    item = {
        'post_id': post_id,
        'text_detected': text_detected,
        'caption': caption,
        'transcript': transcript,
        'social': 'instagram'
    }
    utils.save_or_append(item)
    return item


def instagram_start(post_url: str):
    print('Started Instagram scraping')
    short_code = get_short_code(post_url)
    if not short_code:
        raise ValueError('Error with the post url')
    post_id = f'instagram_{short_code}'
    if utils.is_exists(post_id):
        return utils.is_exists(post_id)
    L = Instaloader()
    post = Post.from_shortcode(L.context, short_code)
    L.download_post(post, target=short_code)
    #-------------------------------
    try:
        shutil.move(short_code, CURRENT_DIR)
    except:
        shutil.rmtree(short_code)
    POST_FOLDER = os.path.join(CURRENT_DIR, short_code)
    POST_FOLDER_IMAGES = os.path.join(POST_FOLDER, 'images')
    os.makedirs(POST_FOLDER_IMAGES, exist_ok=True)
    #_-----------------------------
    files = os.listdir(POST_FOLDER)
    for file in files:
        file_path = os.path.join(POST_FOLDER, file)
        if file_path.endswith('.jpg'):
            try:
                shutil.move(file_path, POST_FOLDER_IMAGES)
            except:
                pass
    caption = post.caption
    item = start_the_tasks(post_id, short_code, caption, POST_FOLDER, POST_FOLDER_IMAGES)
    return item
    

def main(post_url: str):
    try:
        return instagram_start(post_url)
    except Exception as e:
        print(f'Error: {e}')
        return None


if __name__ == '__main__':
    item = main('https://www.instagram.com/hind_hela/reel/DEK5DoDoWA2/')
    print(item)
