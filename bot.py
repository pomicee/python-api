import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
import urllib.parse

CLIENT_ID = 'your_actual_client_id'
CLIENT_SECRET = 'your_actual_client_secret'

def get_access_token():
    try:
        client = BackendApplicationClient(client_id=CLIENT_ID)
        oauth = OAuth2Session(client=client)
        token_url = 'https://accounts.spotify.com/api/token'
        token = oauth.fetch_token(token_url, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        return token['access_token']
    except Exception as e:
        print(f"Error obtaining access token: {e}")
        return None

def search_spotify(query, search_type='artist'):
    access_token = get_access_token()
    if not access_token:
        print("Failed to obtain access token.")
        return None
    query = urllib.parse.quote(query)
    url = f"https://api.spotify.com/v1/search?q={query}&type={search_type}&limit=1"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        search_results = response.json()
        items = search_results[search_type + 's']['items']
        if items:
            return items[0]
        else:
            print(f"No {search_type} found for the query: {query}")
            return None
    else:
        print(f"Search failed. Status code: {response.status_code}")
        print(response.json())
        return None

def get_artist_followers(artist_name):
    artist_data = search_spotify(artist_name, search_type='artist')
    if artist_data:
        followers_count = artist_data['followers']['total']
        return followers_count
    return None

def main():
    artist_name = input("Enter the name of the artist: ").strip()
    try:
        followers = get_artist_followers(artist_name)
        if followers is not None:
            print(f"Followers count for {artist_name}: {followers}")
        else:
            print("Could not fetch followers count.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
