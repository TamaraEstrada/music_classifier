from model import KNNClassifier
from feature_extractor import FeatureExtractor
import os
from dotenv import load_dotenv
import numpy as np
import librosa
from spotify_api import get_token, get_spotify_recommendations, get_valid_spotify_genre, search_tracks_by_genre
from auth_server import get_spotify_auth_code


# Load environment variables at the start
load_dotenv()

def get_spotify_token():
    """Get Spotify token using environment variables"""
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in environment variables")
    
    print("Authenticating with Spotify...")
    auth_code, redirect_uri = get_spotify_auth_code(client_id)
    return get_token(auth_code=auth_code, redirect_uri=redirect_uri)

def get_genre_name(genre_id):
    """Convert numeric genre ID to genre name"""
    genre_mapping = {
        1: "pop",
        2: "classical",
        3: "rock",
        4: "jazz",
        5: "electronic",
        6: "hip-hop",
        7: "country",
        8: "blues",
        9: "reggae",
        10: "latin"
    }
    return genre_mapping.get(genre_id, "other")


def process_local_audio(file_path):
    """Process a local audio file and extract features."""
    try:
        # Load the audio file with librosa
        y, sr = librosa.load(file_path)
        
        # Extract MFCC features
        mfcc_feat = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        
        # Calculate statistical features
        mean_matrix = np.mean(mfcc_feat.T, axis=0)
        covariance = np.cov(mfcc_feat)
        # Create default HMM features (for compatibility with your model)
        hmm_features = np.zeros(10)
        
        return (mean_matrix, covariance, hmm_features)
    except Exception as e:
        print(f"Error processing audio file {file_path}: {str(e)}")
        return None

def analyze_local_songs(classifier, new_songs_dir):
    """Analyze songs from the local directory using the pretrained model"""
    genre_counts = {}
    processed_files = 0
    supported_extensions = ('.mp3', '.wav', '.m4a', '.flac')
    
    print("\nAnalyzing songs from local directory...")
    
    for root, _, files in os.walk(new_songs_dir):
        for file in files:
            if file.lower().endswith(supported_extensions):
                file_path = os.path.join(root, file)
                print(f"\nProcessing: {file}")
                
                try:
                    # Extract features
                    features = process_local_audio(file_path)
                    
                    if features is not None:
                        # Predict genre using your pretrained model
                        predicted_genre_id = classifier.predict(features)
                        genre_name = get_genre_name(predicted_genre_id)
                        
                        if predicted_genre_id:
                            genre_counts[genre_name] = genre_counts.get(genre_name, 0) + 1
                            processed_files += 1
                            print(f"Classified as: {predicted_genre_id} ({genre_name})")
                    
                except Exception as e:
                    print(f"Error processing {file}: {str(e)}")
                    continue
    
    return genre_counts, processed_files

def main():
    # Load the pretrained model
    print("Loading pretrained genre classifier...")
    classifier = KNNClassifier(k=5)
    training_size, test_size = classifier.load_dataset('dataset.dat')
    print(f"Loaded model with {training_size} training samples")
    
    # Set path to new songs directory
    new_songs_dir = os.path.join(os.getcwd(), 'newsongs')
    if not os.path.exists(new_songs_dir):
        print(f"Error: new_songs directory not found at {new_songs_dir}")
        return
    
    # Analyze local songs
    genre_counts, processed_files = analyze_local_songs(classifier, new_songs_dir)
    
    if processed_files == 0:
        print("\nNo audio files could be analyzed. Exiting...")
        return
    
    # Show results
    print(f"\nSuccessfully analyzed {processed_files} tracks")
    
    print("\nGenre distribution:")
    total_tracks = sum(genre_counts.values())
    for genre, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_tracks) * 100
        print(f"{genre}: {count} tracks ({percentage:.1f}%)")
    
    # Calculate majority genre (now working with string genre names)
    majority_genre = max(genre_counts.items(), key=lambda x: x[1])[0]
    spotify_genre = get_valid_spotify_genre(majority_genre)
    print(f"\nDominant genre: {majority_genre} (Spotify genre: {spotify_genre})")
        
    print("\nConnecting to Spotify for similar tracks...")
    try:
        token = get_spotify_token()
        
        if token:
            print("\nSearching for tracks based on your music collection...")
            
            # Try genres in order of frequency
            found_tracks = []
            genres_to_try = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
            
            for genre, count in genres_to_try:
                print(f"\nSearching for {genre} tracks ({count} in your collection)...")
                tracks = search_tracks_by_genre(token, genre)
                
                if tracks:
                    print(f"\nFound tracks matching {genre}:")
                    for i, track in enumerate(tracks, 1):
                        artists = ", ".join(artist['name'] for artist in track['artists'])
                        print(f"\n{i}. {track['name']} by {artists}")
                        
                        if track.get('external_urls', {}).get('spotify'):
                            print(f"   Listen: {track['external_urls']['spotify']}")
                        
                        if track.get('preview_url'):
                            print(f"   Preview: {track['preview_url']}")
                        
                        if track.get('popularity'):
                            print(f"   Popularity: {track['popularity']}/100")
                    
                    found_tracks = tracks
                    break
                else:
                    print(f"No tracks found for {genre}, trying next genre...")
            
            if not found_tracks:
                print("\nCould not find any matching tracks.")
                print("Tried genres:", ", ".join(genre for genre, _ in genres_to_try))
                
        else:
            print("Failed to get Spotify authentication token. Exiting...")
    
    except Exception as e:
        print(f"Error connecting to Spotify: {str(e)}")
        print("Please check your Spotify API credentials and permissions.")

if __name__ == "__main__":
    main()