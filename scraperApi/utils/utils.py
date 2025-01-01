import cv2
from pathlib import Path
import os
import pytesseract
from PIL import Image
import pandas as pd
import concurrent.futures
from paddleocr import PaddleOCR
from openai import OpenAI

ocr = PaddleOCR(use_angle_cls=True, lang='en')

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = Path(CURRENT_DIR).parent.as_posix()
os.makedirs(os.path.join(PARENT_DIR, 'outputs'), exist_ok=True)
OUTPUT_FILE = os.path.join(PARENT_DIR, 'outputs/outputs.csv')


def ocr_image(ocr, image_path):
    text = ''
    try:
        result = ocr.ocr(image_path, cls=True)
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
        if Path(OUTPUT_FILE).exists():
            df = pd.read_csv(OUTPUT_FILE)
            filtered_df = df[df['post_id'] == post_id]
            if filtered_df.empty:
                return False
            return filtered_df.iloc[0, :].to_dict()
        else:
            return False
    except:
        return False


def save_or_append(item: dict):
    df = pd.DataFrame(item, index=[0])
    if Path(OUTPUT_FILE).exists():
        df.to_csv(OUTPUT_FILE, index=False, header=None, mode='a')
    else:
        df.to_csv(OUTPUT_FILE, index=False)

#extract frame from videos
def extract_frames(video_file: str, video_name: str) -> str:
    current_dir_parent = Path(os.path.dirname(os.path.abspath(__file__))).parent.as_posix()
    frame_dir = os.path.join(current_dir_parent, 'frames')
    Path(frame_dir).mkdir(exist_ok=True)
    cap = cv2.VideoCapture(video_file)
    frame_rate = 1  # Desired frame rate (1 frame every 0.5 seconds)
    frame_count = 0
    output_directory = os.path.join(frame_dir, f'{video_name}_frames')
    os.makedirs(output_directory, exist_ok=True)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1
        # Only extract frames at the desired frame rate
        if frame_count % int(cap.get(5) / frame_rate) == 0:
            output_file = f"{output_directory}/frame_{frame_count}.png"
            cv2.imwrite(output_file, frame)
            print(f"Frame {frame_count} has been extracted and saved as {output_file}")
    
    cap.release()
    cv2.destroyAllWindows()
    return output_directory


#convert image to text
def convert_image_to_text(folder: str):
    image_path = os.listdir(folder)
    final_text = ''
    for idx, img in enumerate(image_path):
        image_text = ocr_image(ocr, f'{folder}/{img}')
        print(f'Image {idx}', image_text)
        if image_text not in final_text:
            final_text += f' {image_text}'
    return final_text.strip()


# text = convert_image_to_text('/home/projects/Instagram-scraper-v1/scraperApi/frames/DED66unSaxr_frames')
# print(f'Final: {text}')