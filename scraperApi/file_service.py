import os
from pathlib import Path
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

class FileService():
    def __init__(self):
        self.folder = os.path.join(CURRENT_DIR, 'outputs')
        Path(self.folder).mkdir(exist_ok=True)
        self.image_folder = os.path.join(self.folder, 'images')
        Path(self.image_folder).mkdir(exist_ok=True)
        self.video_folder = os.path.join(self.folder, 'videos')
        Path(self.video_folder).mkdir(exist_ok=True)

    
    def process_video_file(self, result: dict):
        video_url = result.get('video')
        post_id = result.get('post_id')
        folder = os.path.join(self.video_folder, post_id)
        Path(folder).mkdir(exist_ok=True)
        file_name = f'{folder}/video.mp4'
        r = requests.get(video_url, stream = True)
        with open(file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size = 1024*1024): 
                if chunk: 
                    f.write(chunk)
        return file_name
    

    def process_image_file(self, result: dict):
        images = result.get('images')
        post_id = result.get('post_id')
        folder = os.path.join(self.image_folder, post_id)
        Path(folder).mkdir(exist_ok=True)
        for idx, image in enumerate(images):
            file_name = os.path.join(folder, f'{idx}.png')
            response = requests.get(image)
            with open(file_name, 'wb') as f:
                f.write(response.content)
        return folder
