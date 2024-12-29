import sys
import os
from pathlib import Path
sys.path.append(Path(os.getcwd()).parent.as_posix())
#-------------------------
import utils.utils as utils
import re
import pandas as pd
import pyktok as pyk
from config import config
from openai import OpenAI
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
import browser_cookie3
pyk.specify_browser('firefox')

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TIKTOK_OUTPUT_FILE = os.path.join(CURRENT_DIR, 'video_data.csv')
VIDEOS_FOLDER = os.path.join(CURRENT_DIR, 'videos')
Path(VIDEOS_FOLDER).mkdir(exist_ok=True)

#extract video_id and username from tiktok url
def extract_tiktok_info(url):
    pattern = r'https?://(?:www\.)?tiktok\.com/@([^/]+)/video/(\d+)(?:\?.*)?'
    match = re.match(pattern, url)
    if match:
        username = match.group(1)
        video_id = match.group(2)
        return {
            "username": username,
            "video_id": int(video_id)
        }
    else:
        return {}


def tiktok_video_to_text(video_name: str, video_file: str) -> str|None:
    try:
        frames_folder = utils.extract_frames(video_file, video_name)
        text_detected = utils.convert_image_to_text(frames_folder)
        return text_detected
    except Exception as e:
        print(f'Error: {e}')
        return None

 
def tiktok_caption(video_id: int) -> str|None:
    #OUTPUT_FILE = 'tiktok_video_data.csv'
    if Path(TIKTOK_OUTPUT_FILE).exists():
        try:
            df = pd.read_csv(TIKTOK_OUTPUT_FILE)
            return df.loc[df['video_id'] == video_id, 'video_description'].iloc[0]
        except Exception as e:
            print(f'Error: {e}')
            return None
    else:
        return None
    

def tiktok_transcript(video_file: str) -> str|None:
    print(f'Starting Transcription')
    try:
        client = OpenAI(
            api_key=config.OPENAI_API_KEY
        )
        audio_file= open(video_file, "rb")
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


def start_the_tasks(post_id: str, video_id: int, video_name: str, new_video_file: str):
    with ThreadPoolExecutor() as executor:
        text_detected = executor.submit(tiktok_video_to_text, video_name, new_video_file)
        caption = executor.submit(tiktok_caption, video_id)
        transcript = executor.submit(tiktok_transcript, new_video_file)
    text_detected = text_detected.result()
    caption = caption.result()
    transcript = transcript.result()
    item = {
        'post_id': post_id,
        'text_detected': text_detected,
        'caption': caption,
        'transcript': transcript,
        'social': 'tiktok'
    }
    utils.save_or_append(item)
    return item


def tiktok_start(post_url: str):
    url_info = extract_tiktok_info(post_url)
    username = url_info.get('username')
    video_id = url_info.get('video_id')
    if (url_info.get('username')) and (url_info.get('video_id')):
        post_id = f'{username}_{video_id}'
        if utils.is_exists(post_id):
            return utils.is_exists(post_id)
        else:
            video_name = f'@{username}_video_{video_id}'
            video_file = f'@{username}_video_{video_id}.mp4'
            try:
                pyk.save_tiktok(
                    post_url,
                    True,
                    TIKTOK_OUTPUT_FILE,
                    'firefox'
                )
                shutil.move(video_file, VIDEOS_FOLDER)
                print(f'Done saving the tiktok post')
                new_video_file = os.path.join(VIDEOS_FOLDER, video_file)
                item = start_the_tasks(post_id, video_id, video_name, new_video_file)
                return item
            except Exception as e:
                print(f'Error extracting the data: {e}')
                return {}
    else:
        print(f'Error with the url: {post_url}')
        return {}


def main(post_url: str):
    Path(VIDEOS_FOLDER).mkdir(exist_ok=True)
    return tiktok_start(post_url)


if __name__ == '__main__':
    #pyk.specify_browser('firefox')
    item = tiktok_start('https://www.tiktok.com/@micro2rouen/video/7444916723704171798?is_from_webapp=1')
    print(item)