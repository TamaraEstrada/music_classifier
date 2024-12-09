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
        json_result = json.loads(result.content)
        return json_result["access_token"]

    def get_auth_header(self, token):
        return {"Authorization": "Bearer " + token}

    def get_user_playlists(self, token):
        url = "https://api.spotify.com/v1/me/playlists"
        headers = self.get_auth_header(token)
        
        try:
            result = get(url, headers=headers)
            if result.status_code != 200:
                print(f"Error fetching playlists: {result.status_code}")
                print(f"Response: {result.text}")
                return []
                
            json_result = json.loads(result.content)
            if "items" not in json_result:
                print("No playlists found")
                return []
                
            # Filter out any None values or playlists without names
            playlists = [
                playlist for playlist in json_result["items"]
                if playlist is not None and "name" in playlist
            ]
            
            return playlists
            
        except Exception as e:
            print(f"Error processing playlists: {str(e)}")
            return []

    def get_playlist_tracks(self, token, playlist_id):
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = self.get_auth_header(token)

        result = get(url, headers=headers)
        json_result = json.loads(result.content)["items"]
        
        tracks = []
        for item in json_result:
            if item["track"]:
                tracks.append(item["track"])
        
        return tracks

# Create instance and export functions
spotify = SpotifyAPI()
get_token = spotify.get_token
get_user_playlists = spotify.get_user_playlists
get_playlist_tracks = spotify.get_playlist_tracks