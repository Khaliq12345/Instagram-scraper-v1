from googlesearch import search


def parse_response(responses):
    for response in responses:
        idds = response.split('/locations/')
        link_id = idds[1].split('/')[0]
        return link_id

#username = 'selmanmarrakech'
def get_id(place_username:str):
    responses = search(f"site:instagram.com/explore/locations {place_username}", num_results=1)
    link_id = parse_response(responses)
    if link_id:
        return link_id

    responses = search(f"site:instagram.com/explore/locations https://www.instagram.com/{place_username}", num_results=1)
    link_id = parse_response(responses)
    if link_id:
        return link_id