from paddleocr import PaddleOCR
import cv2
import time
from concurrent.futures import ThreadPoolExecutor

image_paths = [
    "/home/projects/Instagram-scraper-v1/scraperApi/frames/@micro2rouen_video_7444916723704171798_frames/frame_1140.png",
    "/home/projects/Instagram-scraper-v1/scraperApi/frames/@micro2rouen_video_7444916723704171798_frames/frame_1380.png"
]
ocr = PaddleOCR(use_angle_cls=True, lang='en')

def image_to_text(ocr, image_path):
    result = ocr.ocr(image_path, cls=True)
    for idx in range(len(result)):
        res = result[idx]
        for line in res:
            print(line[-1][0])


start = time.time()
for image_path in image_paths:
    (ocr, image_path)

end = time.time()
print(end - start)