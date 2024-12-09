from spotify_api import get_token, get_user_playlists, get_playlist_tracks
from auth_server import get_spotify_auth_code
from genre_classifier import process_playlist_tracks
import os
from genre_classifier import process_playlist_tracks, get_recommendations, print_debug_info

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

def main():
    # Get user's playlist and recommend songs
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

    # Retrieve and analyze the tracks
    playlist_tracks = get_playlist_tracks(token, selected_playlist['id'])
    
    if not playlist_tracks:
        print("No tracks found in the selected playlist.")
        return

    print(f"\nAnalyzing {len(playlist_tracks)} tracks from '{selected_playlist['name']}'...")
    genre_counts, processed_tracks = process_playlist_tracks(playlist_tracks, token)

    if processed_tracks == 0:
        print("\nCould not analyze any tracks in the playlist.")
        return

    # Show results
    print(f"\nSuccessfully analyzed {processed_tracks} tracks")
    
    print("\nGenre distribution:")
    total_tracks = sum(genre_counts.values())
    for genre, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_tracks) * 100
        print(f"{genre}: {count} tracks ({percentage:.1f}%)")

    # Calculate majority genre
    majority_genre = max(genre_counts.items(), key=lambda x: x[1])[0]
    print(f"\nDominant genre: {majority_genre}")
    
    # Get recommendations
    print("\nAnalyzing playlist for recommendations...")
    print_debug_info(token, playlist_tracks, majority_genre)
    
    print("\nFinding recommendations based on your playlist...")
    recommendations = get_recommendations(token, playlist_tracks, majority_genre)
    
    if recommendations:
        print("\nRecommended tracks:")
        for i, track in enumerate(recommendations, 1):
            artists = ", ".join(artist['name'] for artist in track['artists'])
            print(f"{i}. {track['name']} by {artists}")
            
            # Add Spotify link if available
            if track.get('external_urls', {}).get('spotify'):
                print(f"   ▶ Listen: {track['external_urls']['spotify']}")
            
            # Add popularity score
            if 'popularity' in track:
                print(f"   ⭐ Popularity: {track['popularity']}/100")
            
            # Add preview URL if available
            if track.get('preview_url'):
                print(f"   🎵 Preview: {track['preview_url']}")
            
            print()  # Add blank line between recommendations
    else:
        print("\nNo recommendations found. Try a different playlist or genre.")

if __name__ == "__main__":
    main()