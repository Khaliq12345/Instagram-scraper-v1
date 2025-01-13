import cv2
import os
from openai import OpenAI
import supabase
import re
import httpx
import sys, pathlib
sys.path.append(pathlib.Path(os.getcwd()).parent.as_posix())
from config.config import SUPABASE_KEY, SUPABASE_URL, OPENAI_API_KEY, PROXY_PASSWORD, PROXY_USERNAME
import easyocr


def ocr_image(reader, image):
    text = ''
    try:
        outputs = reader.readtext(image, detail=0)
        text = ' '.join(outputs)
    except:
        pass
    return text


def is_exists(post_id: str, table: str = 'scraper_out'):
    try:
        client = supabase.Client(SUPABASE_URL, SUPABASE_KEY)
        response = client.table(table).select('*').eq('post_id', post_id).execute()
        if response.data:
            return response.data[0]
        else:
            return False
    except Exception as e:
        print(f'Error: {e}')
        return False


def save_or_append(item: dict, table: str = 'scraper_out'):
    try:
        client = supabase.Client(SUPABASE_URL, SUPABASE_KEY)
        client.table(table).insert(item).execute()
    except Exception as e:
        print(f'Error: {e}')


#extract frame from videos
def extract_frames(video_file: str) -> str:
    reader = easyocr.Reader(['en', 'de'])
    frame_text = ''
    cap = cv2.VideoCapture(video_file)
    frame_rate = 1  # Desired frame rate (1 frame every 0.5 seconds)
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1
        # Only extract frames at the desired frame rate
        if frame_count % int(cap.get(5) / frame_rate) == 0:
            gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            ocr_text = ocr_image(reader, gray_image)
            if ocr_text not in frame_text:
                frame_text += f' {ocr_text}'
    cap.release()
    cv2.destroyAllWindows()
    return frame_text


#convert image to text
def convert_image_to_text(folder: str):
    reader = easyocr.Reader(['en', 'de'])
    image_path = os.listdir(folder)
    final_text = ''
    for idx, img in enumerate(image_path):
        image_text = ocr_image(reader, f'{folder}/{img}')
        print(f'Image {idx}', image_text)
        if image_text not in final_text:
            final_text += f' {image_text}'
    return final_text.strip()


def transcribe_video(video_file: str):
    try:
        client = OpenAI(
            api_key=OPENAI_API_KEY
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


def extract_tiktok_id(post_url):
    if '//vm.' in post_url:
        response = httpx.get(
            post_url,
            timeout=None,
            follow_redirects=True
        )
        post_url = str(response.url)
    pattern = r'https?://(?:www\.)?tiktok\.com/@([^/]+)/(?:video|photo)/(\d+)(?:\?.*)?'
    match = re.match(pattern, post_url)
    if match:
        pid = match.group(2)
        return pid
    else:
        return None


def extract_instagram_id(post_url: str) -> str|None:
    pattern = r'/(?:reel|p)/([a-zA-Z0-9_-]+)'
    match = re.search(pattern, post_url)
    if match:
        return match.group(1)
    else:
        return None


#print(extract_frames('/root/projects/Instagram-scraper-v1/scraperApi/outputs/videos/tiktok_7363316545226935585/video.mp4'))
