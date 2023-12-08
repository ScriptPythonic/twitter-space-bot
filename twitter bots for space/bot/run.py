import requests
import os
import json


bearer_token ="AAAAAAAAAAAAAAAAAAAAAAD0pwEAAAAAzMyx25jM6muo7BvUhUcneldRIyQ%3DfszNn1wi14oeNL0DNzTrYgQjnEnARRtHVx1faO57PQiIqe5uip"
search_url = "https://api.twitter.com/2/spaces/search"

search_term = 'NBA'

query_params = {'query': search_term,  "space.fields": "created_at,lang,invited_user_ids,participant_count,scheduled_start,started_at,title,topic_ids,updated_at,speaker_ids,ended_at","user.fields": "created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,verified_type,withheld", "expansions": "host_ids,topic_ids,invited_user_ids,creator_id,speaker_ids"}

def create_headers(bearer_token):
    headers = {
        "Authorization": "Bearer {}".format(bearer_token),
        "User-Agent": "v2SpacesSearchPython"
    }
    return headers


def connect_to_endpoint(url, headers, params):
    response = requests.request("GET", search_url, headers=headers, params=params)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


def main():
    headers = create_headers(bearer_token)
    json_response = connect_to_endpoint(search_url, headers, query_params)
    print(json.dumps(json_response, indent=4, sort_keys=True))


if __name__ == "_main_":
    main()
    