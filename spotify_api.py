import os
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import json
from pathlib import Path

load_dotenv("secrets.env")

# Удаляем кэш при запуске
CACHE_FILE = Path("spotify_cache.json")
if CACHE_FILE.exists():
    try:
        os.remove(CACHE_FILE)
        print("Кэш удален для получения свежих данных.")
    except Exception as e:
        print(f"Ошибка удаления кэша: {e}")

# Настройка Spotify API
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="1920244aeda1435391174da2822b29d3",
    client_secret="01a39573495143699efe5f598af06ae4",
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-library-read user-modify-playback-state playlist-read-private user-read-playback-state"
))

def load_cache():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Ошибка чтения кэша. Файл поврежден.")
            return None
    return None

def save_cache(liked, playlists):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"liked": liked, "playlists": playlists}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения кэша: {e}")

def fetch_data(limit=50, offset=0):
    try:
        cache = load_cache()
        if cache:
            return cache["liked"], cache["playlists"]
    except:
        pass

    try:
        # Получаем лайкнутые треки
        liked_tracks = sp.current_user_saved_tracks(limit=limit, offset=offset)
        liked = [(track['track']['name'], track['track']['uri']) for track in liked_tracks['items']]

        while liked_tracks['next']:
            offset += limit
            liked_tracks = sp.current_user_saved_tracks(limit=limit, offset=offset)
            liked.extend([(track['track']['name'], track['track']['uri']) for track in liked_tracks['items']])

        # Получаем плейлисты
        playlists = sp.current_user_playlists(limit=50)
        playlist_tracks = []
        for playlist in playlists['items']:
            try:
                tracks = sp.playlist_items(playlist['id'], limit=100)
                playlist_tracks.extend([(f"{playlist['name']} - {track['track']['name']}", track['track']['uri'])
                                        for track in tracks['items'] if track['track']])
            except Exception as e:
                print(f"Ошибка получения плейлиста {playlist['name']}: {e}")

        save_cache(liked, playlist_tracks)
        return liked, playlist_tracks
    except Exception as e:
        print(f"Ошибка получения данных из Spotify: {e}")
        # Пробуем вернуть кэш, если есть
        cache = load_cache()
        if cache:
            return cache["liked"], cache["playlists"]
        return [], []

def search_and_play(query, liked_list, playlist_list, current_playlist="Liked"):
    try:
        query = query.lower()
        if current_playlist == "Liked":
            return [t for t in liked_list if query in t[0].lower()]
        else:
            return [t for t in playlist_list if query in t[0].lower() and t[0].startswith(current_playlist + " -")]
    except Exception as e:
        print(f"Ошибка поиска: {e}")
        return []

def play_track(uri):
    try:
        # Проверяем, что Spotify активен
        devices = sp.devices()
        if not devices['devices']:
            print("Spotify не активен. Запустите Spotify и попробуйте снова.")
            return

        # Добавляем в очередь и переключаем
        sp.add_to_queue(uri)
        sp.next_track()
        print(f"Воспроизведение: {uri}")
    except Exception as e:
        print(f"Ошибка воспроизведения трека: {e}")