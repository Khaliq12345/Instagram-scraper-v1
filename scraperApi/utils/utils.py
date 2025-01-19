import concurrent.futures
import cv2
import os
from openai import OpenAI
import supabase
import re
import httpx
import sys, pathlib
sys.path.append(pathlib.Path(os.getcwd()).parent.as_posix())
from config.config import SUPABASE_KEY, SUPABASE_URL, OPENAI_API_KEY, PROXY_PASSWORD, PROXY_USERNAME
from paddleocr import PaddleOCR
from concurrent.futures import ThreadPoolExecutor
import concurrent
from google.cloud import vision
from google.oauth2 import service_account

CREDENTIALS = service_account.Credentials.from_service_account_file(
	filename='./utils/cred.json',
	scopes=["https://www.googleapis.com/auth/cloud-platform"])


def ocr_image_google(image):
    text = ''
    try:
        client = vision.ImageAnnotatorClient(credentials=CREDENTIALS)
        image = vision.Image(content=image)
        response = client.text_detection(image)
        text = " ".join([x.description for x in response.text_annotations])
        print(text)
        return text
    except:
        pass
    return text

def ocr_image(ocr: PaddleOCR, image):
    text = ''
    try:
        result = ocr.ocr(image, cls=True)
        for idx in range(len(result)):
            res = result[idx]
            try:
                for line in res:
                    text += f' {line[-1][0]}'
            except:
                pass
    except:
        pass
    return text

def is_exists(key: str, value: str, table: str, is_single: bool = True):
    try:
        client = supabase.Client(SUPABASE_URL, SUPABASE_KEY)
        response = client.table(table).select('*').eq(key, value).execute()
        if response.data:
            if is_single:
                return response.data[0]
            else:
                return response.data
        else:
            return False
    except Exception as e:
        print(f'Error: {e}')
        return False

def save_or_append(item: dict|list[dict], table: str):
    try:
        client = supabase.Client(SUPABASE_URL, SUPABASE_KEY)
        client.table(table).insert(item).execute()
    except Exception as e:
        print(f'Error: {e}')

def process_frames_in_order(frames):
    try:
        with ThreadPoolExecutor() as worker:
            futures = [worker.submit(ocr_image_google, frame) for frame in frames]
            future_to_index = {future: idx for idx, future in enumerate(futures)}
            results_with_index = []
            for future in concurrent.futures.as_completed(futures):
                index = future_to_index[future]
                result = future.result()
                results_with_index.append((index, result))
            results_with_index.sort(key=lambda x: x[0])
            frame_text = ''
            for _, ocr_text in results_with_index:
                if ocr_text not in frame_text:
                    frame_text += f' {ocr_text}'
            
            return frame_text.strip()
    except Exception as e:
        print(f'Error: {e}')
        return ''

#extract frame from videos
def extract_frames(video_file: str) -> str:
    cap = cv2.VideoCapture(video_file)
    frame_rate = 1  # Desired frame rate (1 frame every 0.5 seconds)
    frame_count = 0
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1
        # Only extract frames at the desired frame rate
        if frame_count % int(cap.get(5) / frame_rate) == 0:
            success, encoded_image = cv2.imencode('.png', frame)
            if success:
                content = encoded_image.tobytes()
                frames.append(content)
    print(f'Total frames: {len(frames)}')
    frame_text = process_frames_in_order(frames)
    cap.release()
    cv2.destroyAllWindows()
    return frame_text

#convert image to text
def convert_image_to_text(folder: str):
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    image_path = os.listdir(folder)
    final_text = ''
    for idx, img in enumerate(image_path):
        image_text = ocr_image(ocr, f'{folder}/{img}')
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


# video_text = extract_frames('/media/khaliq/New Volume/Documents/Python Projects/khaliq/Upwork Projects/InstagramProject/scraperApi/outputs/videos/tiktok_7363316545226935585/video.mp4')
# print(video_text)
