from src.feature_extractor import FeatureExtractor
from src.model import KNNClassifier
from src.utils import create_genre_mapping
import os

def main():
    # Configuration
    data_directory = "/Users/tamaraestrada/Desktop/music_genre_classifier/Data/genres_original"  # Update this path
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
    
    # Create genre mapping
    genre_mapping = create_genre_mapping(data_directory)
    
    # Now you can use the classifier to predict new audio files
    print("\nModel is ready to classify new audio files!")

if __name__ == "__main__":
    main()