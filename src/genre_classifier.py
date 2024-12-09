from requests import get
import json

def get_track_info(token, track_id):
    """Get basic track information including artist details"""
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = {"Authorization": "Bearer " + token}
    
    result = get(url, headers=headers)
    if result.status_code == 200:
        return json.loads(result.content)
    return None

def get_artist_info(token, artist_id):
    """Get artist genres and other metadata"""
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = {"Authorization": "Bearer " + token}
    
    result = get(url, headers=headers)
    if result.status_code == 200:
        return json.loads(result.content)
    return None

def classify_genre(token, track):
    """Classify a track's genre based on artist and track metadata"""
    try:
        # Get artist information
        artist_id = track['artists'][0]['id']
        artist_info = get_artist_info(token, artist_id)
        
        if artist_info and 'genres' in artist_info and artist_info['genres']:
            # Use the artist's primary genre
            return artist_info['genres'][0]
        
        # Fallback classification based on track properties
        track_info = get_track_info(token, track['id'])
        if track_info:
            if track_info['popularity'] > 80:
                return 'pop'
            elif 'acoustic' in track['name'].lower():
                return 'acoustic'
            elif any(word in track['name'].lower() for word in ['rock', 'metal', 'punk']):
                return 'rock'
            elif any(word in track['name'].lower() for word in ['rap', 'hip', 'trap']):
                return 'hip-hop'
            
        return 'other'
        
    except Exception as e:
        print(f"Error classifying track: {str(e)}")
        return None

def process_playlist_tracks(playlist_tracks, token):
    """Process tracks using simplified genre classification"""
    genre_counts = {}
    processed_tracks = 0
    
    print("\nAnalyzing tracks:")
    for i, track in enumerate(playlist_tracks, 1):
        try:
            track_name = track['name']
            artists = ", ".join([artist['name'] for artist in track['artists']])
            
            print(f"  {i}. {track_name} by {artists}: ", end='', flush=True)
            
            genre = classify_genre(token, track)
            if genre:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
                processed_tracks += 1
                print(f"Classified as {genre}")
            else:
                print("Could not determine genre")
                
        except Exception as e:
            print(f"Error: {str(e)}")
            continue
    
    return genre_counts, processed_tracks

def simplify_genre(genre):
    """Convert specific sub-genres into main genre categories"""
    genre = genre.lower()
    
    if any(pop in genre for pop in ['pop', 'k-pop']):
        return 'pop'
    elif any(rock in genre for rock in ['rock', 'grunge', 'indie']):
        return 'rock'
    elif any(rb in genre for rb in ['r&b', 'rnb']):
        return 'r&b'
    elif 'hip hop' in genre or 'rap' in genre:
        return 'hip-hop'
    elif 'electronic' in genre or 'edm' in genre:
        return 'electronic'
    else:
        return genre

def print_debug_info(token, tracks, majority_genre):
    """Print debug information about the recommendation request"""
    print("\nDebug Information:")
    print(f"Majority Genre: {majority_genre}")
    
    # Print first few tracks
    print("\nSample Tracks:")
    for i, track in enumerate(tracks[:3]):
        print(f"Track {i+1}:")
        print(f"  ID: {track['id']}")
        print(f"  Name: {track['name']}")
        print(f"  Artists: {[artist['name'] for artist in track['artists']]}")
        
        # Get artist genres
        if track['artists']:
            artist_id = track['artists'][0]['id']
            artist_info = get_artist_info(token, artist_id)
            if artist_info and 'genres' in artist_info:
                print(f"  Artist Genres: {artist_info['genres']}")


def get_recommendations(token, tracks, majority_genre):
    """Get recommendations using Spotify search and similar artists"""
    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}

    # Keep track of existing songs and artists
    existing_songs = {track['name'].lower() for track in tracks}
    existing_artists = {artist['name'] for track in tracks for artist in track['artists']}
    
    # Get top artists from your playlist for finding similar music
    top_artists = list(existing_artists)[:5]
    recommended_tracks = []

    for artist in top_artists:
        try:
            # Search for tracks similar to the artist's style but not by them
            params = {
                "q": f"genre:{majority_genre} NOT artist:{artist}",
                "type": "track",
                "limit": 10,
                "market": "US"
            }
            
            print(f"Searching for {majority_genre} tracks similar to {artist}'s style...")
            response = get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                tracks = response.json().get('tracks', {}).get('items', [])
                
                # Filter for new songs not in the original playlist
                for track in tracks:
                    track_name = track['name'].lower()
                    track_artists = {artist['name'] for artist in track['artists']}
                    
                    if (track_name not in existing_songs and 
                        not track_artists.intersection(existing_artists) and
                        track.get('popularity', 0) > 50):  # Popular tracks only
                        recommended_tracks.append(track)
                        existing_songs.add(track_name)
                        if len(recommended_tracks) >= 5:
                            break
                        
        except Exception as e:
            print(f"Error finding recommendations: {str(e)}")
            continue

    # If we still need more recommendations, try a broader genre search
    if len(recommended_tracks) < 5:
        try:
            params = {
                "q": f"genre:{majority_genre}",
                "type": "track",
                "limit": 20,
                "market": "US"
            }
            
            print(f"Searching for additional {majority_genre} tracks...")
            response = get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                tracks = response.json().get('tracks', {}).get('items', [])
                
                for track in tracks:
                    track_name = track['name'].lower()
                    track_artists = {artist['name'] for artist in track['artists']}
                    
                    if (track_name not in existing_songs and 
                        not track_artists.intersection(existing_artists) and
                        track.get('popularity', 0) > 50):
                        recommended_tracks.append(track)
                        existing_songs.add(track_name)
                        if len(recommended_tracks) >= 5:
                            break

        except Exception as e:
            print(f"Error in genre search: {str(e)}")

    return recommended_tracks[:5]


def get_valid_spotify_genre(genre):
    """Convert our genre classifications to valid Spotify genre seeds"""
    genre = genre.lower()
    
    # Mapping of our genres to Spotify's accepted genre seeds
    genre_mapping = {
        'pop': 'pop',
        'art pop': 'pop',
        'social media pop': 'pop',
        'k-pop': 'k-pop',
        'sunshine pop': 'pop',
        'bedroom pop': 'pop',
        'grunge': 'rock',
        'rock': 'rock',
        'indie': 'indie',
        'brighton indie': 'indie',
        'canadian contemporary r&b': 'r-n-b',
        'r&b': 'r-n-b',
        'madchester': 'rock',
        'alt z': 'alternative',
        'other': 'pop'  # Default to pop if unknown
    }
    
    return genre_mapping.get(genre, 'pop')