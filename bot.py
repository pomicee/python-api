import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
import urllib.parse
import logging
import coloredlogs
from flask import Flask, jsonify, request

coloredlogs.install(level='INFO', fmt='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger()

CLIENT_ID = ''  
CLIENT_SECRET = ''  
LASTFM_API_KEY = ''  

app = Flask(__name__)

def get_access_token():
    try:
        client = BackendApplicationClient(client_id=CLIENT_ID)
        oauth = OAuth2Session(client=client)
        token_url = 'https://accounts.spotify.com/api/token'
        token = oauth.fetch_token(token_url, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        logger.info("Successfully obtained access token for Spotify.")
        return token['access_token']
    except Exception as e:
        logger.error(f"Error obtaining access token: {e}")
        return None

def search_spotify(query, search_type='artist'):
    access_token = get_access_token()
    if not access_token:
        logger.error("Failed to obtain access token.")
        return None
    query = urllib.parse.quote(query)
    url = f"https://api.spotify.com/v1/search?q={query}&type={search_type}&limit=1"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        search_results = response.json()
        items = search_results.get(search_type + 's', {}).get('items', [])
        if items:
            logger.info(f"Found {search_type} on Spotify for {query}.")
            return items[0]
        else:
            logger.warning(f"No {search_type} found for {query}.")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during Spotify search: {e}")
        return None

def get_related_artists_lastfm(artist_name):
    url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&artist={artist_name}&api_key={LASTFM_API_KEY}&format=json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        related_artists = [artist['name'] for artist in data.get('similarartists', {}).get('artist', [])]
        logger.info(f"Found {len(related_artists)} related artists from Last.fm for {artist_name}.")
        return related_artists
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching related artists from Last.fm: {e}")
        return []

def get_artist_details(artist_name):
    artist_data = search_spotify(artist_name, search_type='artist')
    if artist_data:
        artist_id = artist_data['id']
        followers_count = artist_data['followers']['total'] if 'followers' in artist_data else 0
        genres = artist_data['genres']
        popularity = artist_data['popularity']

        albums_url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?limit=50&include_groups=album,single"
        top_tracks_url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market=US"
        
        access_token = get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        albums_response = requests.get(albums_url, headers=headers)
        top_tracks_response = requests.get(top_tracks_url, headers=headers)

        if albums_response.status_code == 200:
            albums_data = albums_response.json()
            total_albums = len(albums_data['items'])
            total_songs = sum([album['total_tracks'] for album in albums_data['items']])
        else:
            total_albums, total_songs = 0, 0

        if top_tracks_response.status_code == 200:
            top_tracks_data = top_tracks_response.json()
            top_track = top_tracks_data['tracks'][0] if top_tracks_data['tracks'] else None
            highest_performing_song = top_track['name'] if top_track else "No top track available"
        else:
            highest_performing_song = "No top track available"

        related_artists_lastfm = get_related_artists_lastfm(artist_name)

        return {
            'followers': followers_count,
            'total_albums': total_albums,
            'total_songs': total_songs,
            'genres': genres,
            'popularity': popularity,
            'highest_performing_song': highest_performing_song,
            'related_artists_lastfm': related_artists_lastfm
        }
    return None

@app.route('/api/spotify/artist', methods=['GET'])
def api_get_artist_details():
    artist_name = request.args.get('name')
    if not artist_name:
        return jsonify({"error": "Artist name is required"}), 400

    try:
        artist_info = get_artist_details(artist_name)
        if artist_info:
            return jsonify(artist_info)
        else:
            return jsonify({"error": "Could not fetch data for the artist."}), 404
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
