from feature_extractor import FeatureExtractor
from model import KNNClassifier
from utils import create_genre_mapping
from spotify_api import get_token, get_user_playlists, get_playlist_tracks, search_genre
import os
from auth_server import get_spotify_auth_code
import webbrowser
import queue
from spotify_api import get_token, get_user_playlists, get_playlist_tracks, search_genre, get_audio_features, get_track_genre

def process_playlist_tracks(playlist_tracks, token):
    """Process tracks using Spotify's audio features API."""
    genre_counts = {}
    processed_tracks = 0
    
    print("\nAnalyzing tracks:")
    for i, track in enumerate(playlist_tracks, 1):
        try:
            track_id = track['id']
            track_name = track['name']
            artists = ", ".join([artist['name'] for artist in track['artists']])
            
            print(f"  {i}. {track_name} by {artists}: ", end='', flush=True)
            
            # Get audio features for the track
            audio_features = get_audio_features(token, track_id)
            if audio_features:
                genre = get_track_genre(audio_features)
                if genre:
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
                    processed_tracks += 1
                    print(f"Classified as {genre}")
                else:
                    print("Could not determine genre")
            else:
                print("Could not fetch audio features")
                
        except Exception as e:
            print(f"Error: {str(e)}")
            continue
    
    return genre_counts, processed_tracks

def authenticate_spotify():
    """Authenticate with Spotify and return access token"""
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in environment variables")
    
    print("Opening browser for Spotify authentication...")
    try:
        auth_code, redirect_uri = get_spotify_auth_code(client_id)
        print("Authentication successful!")
        return get_token(auth_code=auth_code, redirect_uri=redirect_uri)
    except Exception as e:
        print(f"Authentication failed: {str(e)}")
        return None


# Before the line that calls process_playlist_tracks, the main function should look like this:
def main():
    # Configuration
    data_directory = "/Users/tamaraestrada/Desktop/music_genre_classifier/Data/genres_original"
    features_file = "dataset.dat"

    # Get user's playlist and recommend songs
    print("Opening browser for Spotify authentication...")
    token = authenticate_spotify()
    
    if not token:
        print("Failed to get authentication token. Exiting...")
        return

    playlists = get_user_playlists(token)
    
    if not playlists:
        print("No playlists found. Make sure you have created some playlists in your Spotify account.")
        return
        
    # Display the user's playlists and prompt them to select one
    print("\nAvailable playlists:")
    for i, playlist in enumerate(playlists, 1):
        print(f"{i}. {playlist['name']}")

    while True:
        try:
            playlist_index = int(input("\nEnter the number of the playlist (or 0 to exit): "))
            if playlist_index == 0:
                return
            if 1 <= playlist_index <= len(playlists):
                break
            print(f"Please enter a number between 1 and {len(playlists)}")
        except ValueError:
            print("Please enter a valid number")

    selected_playlist = playlists[playlist_index - 1]
    print(f"\nSelected playlist: {selected_playlist['name']}")

    # Retrieve the tracks from the selected playlist
    playlist_tracks = get_playlist_tracks(token, selected_playlist['id'])
    
    if not playlist_tracks:
        print("No tracks found in the selected playlist.")
        return

    # Process the tracks using audio features
    print(f"\nAnalyzing {len(playlist_tracks)} tracks from '{selected_playlist['name']}'...")
    genre_counts, processed_tracks = process_playlist_tracks(playlist_tracks, token)  # Changed this line

    if processed_tracks == 0:
        print("\nCould not analyze any tracks in the playlist.")
        return

    print(f"\nSuccessfully analyzed {processed_tracks} tracks")
    
    # Find the majority genre
    majority_genre = max(genre_counts.items(), key=lambda x: x[1])[0]
    total_tracks = sum(genre_counts.values())
    
    print("\nGenre distribution:")
    for genre, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_tracks) * 100
        print(f"{genre}: {count} tracks ({percentage:.1f}%)")
    
    print(f"\nDominant genre: {majority_genre}")

    # Get recommendations
    print(f"\nFinding recommendations based on {majority_genre}...")
    recommended_tracks = search_genre(token, majority_genre)
    
    if recommended_tracks:
        print("\nRecommended tracks:")
        artists = ", ".join([artist['name'] for artist in recommended_tracks['artists']])
        print(f"- {recommended_tracks['name']} by {artists}")
    else:
        print("No recommendations found.")


if __name__ == "__main__":
    main()