import pandas as pd
import get_location_id
import get_popular_posts

def start():
    with open('placese.txt', 'r') as f:
        usernames = f.readlines()
        usernames = [txt.strip() for txt in usernames]
    for username in usernames:
        location_id = get_location_id.get_id(username)
        print(f'Username: {username} | Location ID: {location_id}')
        if location_id:
            get_popular_posts.start(location_id, username)


if __name__ == '__main__':
    start()