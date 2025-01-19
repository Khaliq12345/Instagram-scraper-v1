import httpx
from datetime import datetime, timezone
import utils
import utils.utils
from dateparser import parse
from config import config

headers = {
	'x-rapidapi-host': config.RAPID_API_HOST,
	'x-rapidapi-key': config.RAPID_API_KEY
}

def is_expired(date_string: str):
    try:
        date_string = date_string.split('+')[0]
        delta = (datetime.now(timezone.utc) - parse(date_string, region='utc').astimezone(timezone.utc))
        if delta.days > 30:
            return True
        else:
            return False
    except:
        return True
    
def create_place_info(query: str):
    current_utc_time = datetime.now(timezone.utc)
    timestamp_format = "%Y-%m-%d %H:%M:%S"
    formatted_timestamp = current_utc_time.strftime(timestamp_format)
    response = httpx.get(
        url=f'https://local-business-data.p.rapidapi.com/search?query={query}&limit=1&extract_emails_and_contacts=true',
        headers=headers
    )
    if response.status_code == 200:
        json_data = response.json()
        json_data: dict = json_data['data'][0]
        try:
            about_summary = json_data.get['about']['summary']
        except:
            about_summary = None
        if json_data.get('photos_sample'):
            photos_sample = [x.get('photo_url') for x in json_data.get('photos_sample')]
        else:
            photos_sample = []
        item = {
            'place_id': json_data.get('place_id'),
            'name': query,
            'address': json_data.get('full_address'),
            'latitude': json_data.get('latitude'),
            'longitude': json_data.get('longitude'),
            'type': json_data.get('type'),
            'subtypes': json_data.get('subtypes'),
            'rating': json_data.get('rating'),
            'phone': json_data.get('phone_number'),
            'website': json_data.get('website'),
            'price_level': json_data.get('price_level'),
            'updated_at': formatted_timestamp,
            'last_google_sync': formatted_timestamp,
            'google_id': json_data.get('google_id'),
            'district': json_data.get('district'),
            'photo_sample': photos_sample,
            'review_count': json_data.get('review_count'),
            'verified': json_data.get('verified'),
            'buisness_status': json_data.get('buisness_status'),
            'street_address': json_data.get('street_address'),
            'about_summary': about_summary,
            'metadata': json_data,
        }
        return item

def get_place_info(query: str):
    response = utils.utils.is_exists('name', query, 'places')
    if response:
        updated_date = response.get('updated_at')
        if is_expired(updated_date):
            print('Expired, updating')
            item = create_place_info(query)
            utils.utils.save_or_append(item, 'places')
            return item
        else:
            print('Not expired!')
            return response
    else:
        print('New data')
        item = create_place_info(query)
        utils.utils.save_or_append(item, 'places')
        return item

# query = 'SAAN'
# print(get_place_info(query))