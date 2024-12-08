import os
import pickle
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF

class LyricalAnalyzer:
    def __init__(self, data_directory):
        self.directory = data_directory
        self.lyric_features = None
        self.genre_mapping = self.create_genre_mapping()

    def create_genre_mapping(self):
        """Create a mapping between numeric labels and genre names."""
        results = defaultdict(int)
        genres = ['pop', 'rock', 'hiphop', 'classical']  
        for i, genre in enumerate(genres, 1):
            results[i] = genre
        return results

    def extract_lyrical_features(self, output_file="lyrical_features.dat"):
        """Extract lyrical features from song lyrics and save to binary file."""
        lyrical_data = []
        labels = []

        for genre in ["pop", "rock"]:  # Update this list to the genres you want to use
            genre_path = os.path.join(self.directory, genre)
            print(f"Processing folder: {genre}")

            for file in os.listdir(genre_path):
                try:
                    file_path = os.path.join(genre_path, file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lyrics = f.read()
                    lyrical_data.append(lyrics)
                    labels.append(self.genre_mapping[genre])
                except UnicodeDecodeError:
                    print(f"Error decoding {file} in {genre}")
                    continue


        # Extract TF-IDF features from lyrics
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(lyrical_data)
        self.lyric_features = X.toarray()

        # Perform NMF to extract topics from lyrics
        nmf = NMF(n_components=10, random_state=42)
        self.lyric_topics = nmf.fit_transform(self.lyric_features)

        # Save the lyrical features and labels to a binary file
        with open(output_file, "wb") as f:
            pickle.dump((self.lyric_features, self.lyric_topics, labels), f)


    def load_lyrical_features(self, filename):
        """Load lyrical features from the binary file."""
        with open(filename, 'rb') as f:
            self.lyric_features, self.lyric_topics, self.labels = pickle.load(f)
        return self.lyric_features, self.lyric_topics, self.labels

    def get_genre_name(self, label):
        """Retrieve the genre name for a given label."""
        return self.genre_mapping[label]