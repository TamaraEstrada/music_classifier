# src/spotify_api.py
from requests import get, post
import json
import os
import base64
from dotenv import load_dotenv
import urllib.parse


load_dotenv()

def get_token(auth_code=None, redirect_uri=None):
    """Get Spotify access token"""
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("CLIENT_ID and CLIENT_SECRET must be set")
    
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # Try client credentials flow first (simpler)
    data = {"grant_type": "client_credentials"}
    
    try:
        result = post(url, headers=headers, data=data)
        print(f"Token request status: {result.status_code}")
        
        if result.status_code == 200:
            return result.json().get("access_token")
    except Exception as e:
        print(f"Error getting token: {str(e)}")
    
    return None

def is_holiday_song(track):
    """Check if a track is likely a holiday/Christmas song"""
    holiday_keywords = {
        'christmas', 'xmas', 'santa', 'rudolph', 'sleigh',
        'silent night', 'jingle bells'
    }
    
    title = track['name'].lower()
    album_name = track.get('album', {}).get('name', '').lower()
    
    return any(keyword in title or keyword in album_name 
              for keyword in holiday_keywords)
def search_tracks_by_genre(token, genre, min_popularity=50):
    """Search for tracks by genre using Spotify's search endpoint"""
    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}
    
    spotify_genre = get_valid_spotify_genre(genre)
    print(f"Searching for tracks in genre: {spotify_genre}")
    
    params = {
        "q": f"genre:{spotify_genre}",
        "type": "track",
        "market": "US",
        "limit": 50  # Request more tracks to ensure we have enough after filtering
    }
    
    try:
        response = get(url, headers=headers, params=params)
        print(f"Search API call status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            all_tracks = data.get('tracks', {}).get('items', [])
            
            # Filter and sort tracks
            filtered_tracks = []
            for track in all_tracks:
                if (track.get('popularity', 0) >= min_popularity and
                    not is_holiday_song(track)):
                    filtered_tracks.append(track)
            
            # Sort by popularity
            filtered_tracks.sort(key=lambda x: x.get('popularity', 0), reverse=True)
            
            # Take top 10
            final_tracks = filtered_tracks[:10]
            print(f"Found {len(final_tracks)} suitable tracks after filtering")
            
            return final_tracks
        else:
            print(f"Error response: {response.text}")
            return []
            
    except Exception as e:
        print(f"Error searching tracks: {str(e)}")
        return []


def get_valid_spotify_genre(genre):
    """Map our genres to valid Spotify search terms"""
    genre_mapping = {
        'pop': 'pop',
        'rock': 'rock',
        'electronic': 'dance electronic',
        'hip-hop': 'hip hop',
        'classical': 'classical',
        'jazz': 'jazz',
        'blues': 'blues',
        'alternative': 'alternative',
        'indie': 'indie',
        'metal': 'metal'
    }

    mapped_genre = genre_mapping.get(genre.lower(), 'pop')
    print(f"Mapped '{genre}' to search term: '{mapped_genre}'")
    return mapped_genre


# Export the new function instead of the old one
__all__ = ['get_token', 'search_tracks_by_genre', 'get_valid_spotify_genre']