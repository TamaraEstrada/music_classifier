from model import KNNClassifier
from spotify_api import get_token, search_genre
from feature_extractor import FeatureExtractor

# Initialize the classifier
classifier = KNNClassifier(k=5)
classifier.load_dataset("dataset.dat")

def get_user_playlist():
    playlist = []
    print("Enter song names (type 'done' to finish):")
    while True:
        song_name = input("Song name: ")
        if song_name.lower() == "done":
            break
        playlist.append(song_name)
    return playlist

def get_song_files(playlist):
    song_files = []
    token = get_token()
    for song_name in playlist:
        song_data = search_genre(token, song_name)
        if song_data:
            song_files.append(song_data["preview_url"])
        else:
            print(f"Could not find audio file for '{song_name}'")
    return song_files

def classify_playlist(playlist):
    genre_counts = {}  
    extractor = FeatureExtractor("/Users/tamaraestrada/Desktop/music_genre_classifier/dataset.dat")

    for song_name in playlist:
        try:
            # Load the audio file and extract the features
            song_features = extractor.extract_features_for_song(song_name)
            genre = classifier.predict(song_features)
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
        except Exception as e:
            print(f"Error processing '{song_name}': {str(e)}")

    # Determine the majority genre
    majority_genre = max(genre_counts, key=genre_counts.get)
    return majority_genre


def recommend_songs(genre):
    token = get_token()
    recommended_songs = search_genre(token, genre)
    return recommended_songs
