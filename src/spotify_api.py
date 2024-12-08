from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json

load_dotenv()

class SpotifyAPI:
    def __init__(self):
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        
        if self.client_id is None or self.client_secret is None:
            raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in the environment variables")
    
    def get_token(self, auth_code=None, redirect_uri=None):
        """Get Spotify access token using either client credentials or authorization code flow"""
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
        
        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        if auth_code and redirect_uri:
            data = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": redirect_uri
            }
        else:
            data = {"grant_type": "client_credentials"}

        result = post(url, headers=headers, data=data)

        if result.status_code != 200:
            raise Exception(f"Failed to get token: {result.status_code}, {result.text}")
        
        json_result = json.loads(result.content)
        
        if 'access_token' not in json_result:
            raise Exception("The key 'access_token' was not found in the response")
        
        return json_result["access_token"]

    def get_auth_header(self, token):
        return {"Authorization": "Bearer " + token}

    def get_user_playlists(self, token):
        """Get the current user's playlists."""
        url = "https://api.spotify.com/v1/me/playlists"
        headers = self.get_auth_header(token)
        
        result = get(url, headers=headers)
        
        if result.status_code != 200:
            print(f"Error fetching playlists: {result.status_code}")
            print(f"Response: {result.text}")
            return []
        
        try:
            json_result = json.loads(result.content)
            if "items" not in json_result:
                print("No 'items' found in playlist response")
                return []
                
            playlists = [
                playlist for playlist in json_result["items"]
                if playlist is not None and "name" in playlist
            ]
            
            return playlists
            
        except json.JSONDecodeError:
            print("Error decoding JSON response")
            return []
        except Exception as e:
            print(f"Unexpected error fetching playlists: {str(e)}")
            return []

    def get_playlist_tracks(self, token, playlist_id):
        """Get tracks from a specific playlist."""
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = self.get_auth_header(token)

        result = get(url, headers=headers)
        
        if result.status_code != 200:
            print(f"Error fetching tracks: {result.status_code}")
            print(f"Response: {result.text}")
            return []

        try:
            json_result = json.loads(result.content)
            if "items" not in json_result:
                print("No 'items' found in tracks response")
                return []

            tracks = []
            for item in json_result["items"]:
                if item is not None and "track" in item and item["track"] is not None:
                    tracks.append(item["track"])
            
            return tracks
            
        except json.JSONDecodeError:
            print("Error decoding JSON response")
            return []
        except Exception as e:
            print(f"Unexpected error fetching tracks: {str(e)}")
            return []

    def search_genre(self, token, genre):
        """Search for tracks in a specific genre."""
        url = "https://api.spotify.com/v1/search"
        headers = self.get_auth_header(token)
        
        params = {
            "q": f"genre:{genre}", 
            "type": "track",       
            "limit": 10
        }
        
        query = f"?q={params['q']}&type={params['type']}&limit={params['limit']}"
        query_url = url + query
        
        result = get(query_url, headers=headers)
        json_result = json.loads(result.content)["tracks"]["items"]
        
        if len(json_result) == 0:
            print("No tracks found")
            return None
        
        return json_result[0]

# Create a single instance
spotify = SpotifyAPI()

# Create module-level functions that use the instance
def get_token(*args, **kwargs):
    return spotify.get_token(*args, **kwargs)

def get_user_playlists(token):
    return spotify.get_user_playlists(token)

def get_playlist_tracks(token, playlist_id):
    return spotify.get_playlist_tracks(token, playlist_id)

def search_genre(token, genre):
    return spotify.search_genre(token, genre)