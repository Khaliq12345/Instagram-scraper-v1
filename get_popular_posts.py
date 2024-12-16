import requests
import json
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from pathlib import Path
from threading import Lock
from functools import cache
from send_to_supabase import start_importing
import os
from dotenv import load_dotenv

load_dotenv()

lock = Lock()

csrftoken = os.getenv('csrftoken')
sessionid = os.getenv('sessionid')

COOKIES = {
    'csrftoken': csrftoken,
    'sessionid': sessionid,
}

HEADERS = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9,fr;q=0.8',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://www.instagram.com',
    'priority': 'u=1, i',
    'referer': 'https://www.instagram.com/instagram/',
    'sec-ch-prefers-color-scheme': 'dark',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-full-version-list': '"Google Chrome";v="131.0.6778.139", "Chromium";v="131.0.6778.139", "Not_A Brand";v="24.0.0.0"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"Linux"',
    'sec-ch-ua-platform-version': '"6.8.0"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'x-asbd-id': '129477',
    'x-bloks-version-id': '7cebebfbaf5374ad12812342f99c7eb8d130e7e3bb5db252249c30a04cc54795',
    'x-csrftoken': csrftoken,
    'x-fb-friendly-name': 'PolarisProfilePageContentQuery',
    'x-fb-lsd': 'UGfM4EQUrCIieEk3rQ38yF',
    'x-ig-app-id': '936619743392459',
}


def save_single_row(item: dict, fileName: str):
    with lock:
        df = pd.DataFrame(item, index=[0])
        if Path(fileName).exists():
            df.to_csv(fileName, mode='a', index=False, header=False)
        else:
            df.to_csv(fileName, index=False)
        

def get_or_none(json_data, code: str):
    try:
        return eval(code)
    except:
        return None

@cache
def scrape_single_profile(profile_pk: str):
    try:
        print(f'profile: {profile_pk}')
        payload = {"id":profile_pk, "render_surface":"PROFILE"}
        data = {
            'variables': json.dumps(payload),
            'doc_id': '9539110062771438',
        }
        response = requests.post('https://www.instagram.com/graphql/query', cookies=COOKIES, headers=HEADERS, data=data)
        json_data = response.json()
        item = {
            'fullName': get_or_none(json_data, "json_data['data']['user']['full_name']"),
            'bio': get_or_none(json_data, "json_data['data']['user']['biography']"),
            'followersCount': get_or_none(json_data, "json_data['data']['user']['follower_count']"),
        }
        return item
        #save_single_row(item, fileName)
    except Exception as e:
        print(f'Error: {e}')
        return {}
    

def parse_post(post: dict, placeUsername: str):
    json_data = post['node']
    item = {
        'placeUsername': placeUsername,
        'imageUrl': get_or_none(json_data, "json_data['image_versions2']['candidates'][0]['url']"),
        'postId': get_or_none(json_data, "json_data['code']"),
        'postUrl': f"""https://www.instagram.com/oceanelhimer/p/{get_or_none(json_data, "json_data['code']")}/""",
        'likes': get_or_none(json_data, "json_data['like_count']"),
        'date': get_or_none(json_data, "json_data['caption']['created_at']"),
        'caption': get_or_none(json_data, "json_data['caption']['text']"),
        'profile': get_or_none(json_data, "json_data['user']['username']"),
        'profilePk': get_or_none(json_data, "json_data['user']['pk']"),
    }
    return item


def single_post_scraper(post: dict, placeUsername: str):
    result = parse_post(post, placeUsername)
    if result.get('profilePk'):
        profilePk = result.get('profilePk')
        profile = scrape_single_profile(profilePk)
        result['fullName'] = profile.get('fullName')
        result['bio'] = profile.get('bio')
        try:
            result['followersCount'] = int(profile.get('followersCount'))
        except:
            result['followersCount'] = 0
    save_single_row(result, f'{placeUsername}.csv')
    

def scrape_multiple_posts(posts: list[dict], placeUsername: str):
    with ThreadPoolExecutor() as worker:
        for post in posts:
            worker.submit(single_post_scraper, post, placeUsername)
            

def start(locationId: str, placeUsername: str):
    json_payload = {"after":"", "location_id":locationId,"tab":"ranked"}
    data = {
        'variables': json.dumps(json_payload),
        'doc_id': '9161013987244424',
    }
    PAGE_NUM = 4 #Number of page to scrape
    for i in range(PAGE_NUM):
        try:
            print(f'Page: {i}')
            response = requests.post('https://www.instagram.com/graphql/query', cookies=COOKIES, headers=HEADERS, data=data)
            print(f'Response: {response.status_code}')
            json_data = response.json()
            json_info = json_data['data']['xdt_location_get_web_info_tab']
            posts = json_data['data']['xdt_location_get_web_info_tab']['edges']
            if json_info['page_info']['has_next_page']:
                json_payload['after'] = json_info['page_info']['end_cursor']
                data['variables'] = json.dumps(json_payload)
            scrape_multiple_posts(posts, placeUsername)
        except Exception as e:
            print(f'Error: {e}')
        
    start_importing(placeUsername, locationId)
    if Path(f'{placeUsername}.csv').exists():
        os.remove(f'{placeUsername}.csv')
    print('DONE!')
        
        
if __name__ == '__main__':
    start('255261194582405', 'selmanmarrakech')