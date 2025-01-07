import cv2
import os
from paddleocr import PaddleOCR
from openai import OpenAI
import supabase
from config.config import SUPABASE_KEY, SUPABASE_URL, OPENAI_API_KEY, PROXY_PASSWORD, PROXY_USERNAME

ocr = PaddleOCR(use_angle_cls=True, lang='en')


def ocr_image(image):
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


def is_exists(post_id: str):
    try:
        client = supabase.Client(SUPABASE_URL, SUPABASE_KEY)
        response = client.table('scraper_out').select('*').eq('post_id', post_id).execute()
        if response.data:
            return response.data[0]
        else:
            return False
    except Exception as e:
        print(f'Error: {e}')
        return False


def save_or_append(item: dict):
    try:
        client = supabase.Client(SUPABASE_URL, SUPABASE_KEY)
        client.table('scraper_out').insert(item).execute()
    except Exception as e:
        print(f'Error: {e}')


#extract frame from videos
def extract_frames(video_file: str) -> str:
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
            ocr_text = ocr_image(frame)
            frame_text = f' {ocr_text}'
    
    cap.release()
    cv2.destroyAllWindows()
    return frame_text


#convert image to text
def convert_image_to_text(folder: str):
    image_path = os.listdir(folder)
    final_text = ''
    for idx, img in enumerate(image_path):
        image_text = ocr_image(f'{folder}/{img}')
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

# text = convert_image_to_text('/home/projects/Instagram-scraper-v1/scraperApi/frames/DED66unSaxr_frames')
# print(f'Final: {text}')