from feature_extractor import FeatureExtractor
from model import KNNClassifier
from utils import create_genre_mapping
from spotify_api import get_token, get_user_playlists, get_playlist_tracks, search_genre
import os
from auth_server import get_spotify_auth_code
import webbrowser
import queue

def main():
    # Configuration
    data_directory = "/Users/tamaraestrada/Desktop/music_genre_classifier/Data/genres_original"
    features_file = "dataset.dat"

    # Extract features if needed
    if not os.path.exists(features_file):
        print("Extracting features...")
        extractor = FeatureExtractor(data_directory)
        extractor.extract_features(features_file)

    # Train and evaluate model
    print("Training model...")
    classifier = KNNClassifier(k=5)
    train_size, test_size = classifier.load_dataset(features_file)
    print(f"Training set size: {train_size}")
    print(f"Test set size: {test_size}")

    accuracy = classifier.evaluate()
    print(f"Model accuracy: {accuracy:.2%}")

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

    # Retrieve the tracks from the selected playlist
    playlist_tracks = get_playlist_tracks(token, selected_playlist['id'])

    # Classify the songs in the playlist and determine the majority genre
    genre_counts = {}
    extractor = FeatureExtractor(data_directory)
    for track in playlist_tracks:
        try:
            song_features = extractor.extract_features_for_song(track['preview_url'])
            genre = classifier.predict(song_features)
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
        except Exception as e:
            print(f"Error processing '{track['name']}': {str(e)}")

    majority_genre = max(genre_counts, key=genre_counts.get)

    # Recommend songs in the majority genre
    recommended_songs = recommend_songs(token, majority_genre)

    # Present the recommended songs to the user
    print(f"Recommended songs in the '{genre_mapping[majority_genre]}' genre:")
    for song in recommended_songs:
        print(song["name"])

def authenticate_spotify():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in environment variables")
    
    print("Opening browser for Spotify authentication...")
    try:
        auth_code, redirect_uri = get_spotify_auth_code(client_id)
        print("Authentication successful!")
        return get_token(auth_code=auth_code, redirect_uri=redirect_uri)
    except queue.Empty:
        print("Authentication timed out. Please try again.")
        return None
    except Exception as e:
        print(f"Authentication failed: {str(e)}")
        return None
    
def recommend_songs(token, genre):
    recommended_songs = search_genre(token, genre)
    return recommended_songs

if __name__ == "__main__":
    main()