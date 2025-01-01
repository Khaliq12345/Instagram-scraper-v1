import os
from supabase import create_client, Client
import pandas as pd
import json
import os
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv('URL')
KEY = os.getenv('KEY')

supabase: Client = create_client(URL, KEY)

def start_importing(placeUsername: str, locationId: str):
    df = pd.read_csv(f'{placeUsername}.csv')
    df.drop_duplicates(subset=['profilePk'], inplace=True)
    json_string = df.nlargest(10, columns=['followersCount']).to_json(orient='records')
    json_datas = json.loads(json_string)
    for json_data in json_datas:
        try:
            response = (
                supabase.table("posts")
                .insert(json_data)
                .execute()
            )
        except:
            pass

    #Save the username and locationId
    result = {
        'locationId': locationId,
        'placeUsername': placeUsername
    }
    try:
        response = (
            supabase.table("main")
            .insert(result)
            .execute()
        )
    except:
        pass

