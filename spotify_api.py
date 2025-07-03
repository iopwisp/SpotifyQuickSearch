import os

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import json
from pathlib import Path

load_dotenv("secrets.env")

# Настройка Spotify API
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="1920244aeda1435391174da2822b29d3",
    client_secret="01a39573495143699efe5f598af06ae4",
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-library-read user-modify-playback-state playlist-read-private user-read-playback-state"
))
# Кэширование треков
CACHE_FILE = Path("spotify_cache.json")

def load_cache():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_cache(liked, playlists):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({"liked": liked, "playlists": playlists}, f, ensure_ascii=False, indent=2)

async def fetch_data(limit=50, offset=0):
    cache = load_cache()
    if cache:
        return cache["liked"], cache["playlists"]

    liked_tracks = sp.current_user_saved_tracks(limit=limit, offset=offset)
    liked = [(track['track']['name'], track['track']['uri']) for track in liked_tracks['items']]
    while liked_tracks['next']:
        offset += limit
        liked_tracks = sp.current_user_saved_tracks(limit=limit, offset=offset)
        liked.extend([(track['track']['name'], track['track']['uri']) for track in liked_tracks['items']])

    playlists = sp.current_user_playlists(limit=10)
    playlist_tracks = []
    for playlist in playlists['items']:
        tracks = sp.playlist_items(playlist['id'], limit=50)
        playlist_tracks.extend([(f"{playlist['name']} - {track['track']['name']}", track['track']['uri'])
                               for track in tracks['items'] if track['track']])

    save_cache(liked, playlist_tracks)
    return liked, playlist_tracks

def search_and_play(query, liked_list, playlist_list, current_playlist="Liked"):
    if current_playlist == "Liked":
        return [t for t in liked_list if query.lower() in t[0].lower()]
    else:
        return [t for t in playlist_list if query.lower() in t[0].lower() and t[0].startswith(current_playlist + " -")]

def play_track(uri):
    sp.add_to_queue(uri)
    sp.next_track()