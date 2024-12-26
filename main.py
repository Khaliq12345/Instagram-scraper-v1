import pandas as pd
import get_location_id
import get_popular_posts


def is_scraped(username):
    with open('success.txt', 'r') as f:
        usernames = f.readlines()
        usernames = [u.strip() for u in usernames]

    if username in usernames:
        return True
    else:
        return False
    

def start():
    with open('placese.txt', 'r') as f:
        usernames = f.readlines()
        usernames = [txt.strip() for txt in usernames]
    for username in usernames:
        if is_scraped(username):
            print(f'Username ({username}) scraped')
        else:
            try:
                location_id = get_location_id.get_id(username)
                print(f'Username: {username} | Location ID: {location_id}')
                if location_id:
                    get_popular_posts.start(location_id, username)
                with open('success.txt', 'a') as f:
                    f.write(f'{username}\n')
            except:
                with open('fails.txt', 'a') as f:
                    f.write(f'{username}\n')


if __name__ == '__main__':
    start()