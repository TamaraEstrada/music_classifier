from collections import defaultdict
import os

def create_genre_mapping(directory):
    """Create a mapping between numeric labels and genre names."""
    results = defaultdict(int)
    for i, folder in enumerate(os.listdir(directory), 1):
        results[i] = folder
    return results