import numpy as np
import scipy.io.wavfile as wav
from python_speech_features import mfcc
import pickle
import os
from hmmlearn import hmm

class FeatureExtractor:
    def __init__(self, data_directory):
        self.directory = data_directory
        self.hmm_model = self.train_hmm_model()
    
    def train_hmm_model(self):
        """Train an HMM model using the training data."""
        # Load the MFCC features for the training data
        X_train = self.load_mfcc_features("/Users/tamaraestrada/Desktop/music_genre_classifier/dataset.dat")

        # Train the HMM model
        model = hmm.GaussianHMM(n_components=10, covariance_type="diag", n_iter=1000)
        model.fit(X_train)

        return model
    
    def load_mfcc_features(self, file_path):
        """Load MFCC features from the binary file."""
        mfcc_features = []
        with open(file_path, 'rb') as f:
            while True:
                try:
                    mean_matrix, covariance, _ = pickle.load(f)
                    mfcc_features.append((mean_matrix, covariance))
                except EOFError:
                    break
        return np.array(mfcc_features)

    def extract_features(self, output_file="dataset.dat"):
        """Extract MFCC features from audio files and save to binary file."""
        with open(output_file, "wb") as f:
            for i, folder in enumerate(os.listdir(self.directory), 1):
                if i == 11:  # We have 10 genres
                    break
                    
                folder_path = os.path.join(self.directory, folder)
                print(f"Processing folder: {folder}")
                

                hmm_features = self.extract_hmm_features(file_path)

                 # Combine MFCC and HMM-based features
                feature = (mean_matrix, covariance, hmm_features, i)
                pickle.dump(feature, f)

                for file in os.listdir(folder_path):
                    try:
                    # rate: how many measurements per second
                    # sig: amplitude values
                        file_path = os.path.join(folder_path, file)
                        rate, sig = wav.read(file_path)
                    # extracts mfcc features from the signal
                    # returns the matrix where each row is a frame
                    # each column is a mfcc coef
                        mfcc_feat = mfcc(sig, rate, winlen=0.020, appendEnergy=False)
                    # calculates statistical features from mfcc
                    # covariance mat captures relationship between coef
                        covariance = np.cov(np.matrix.transpose(mfcc_feat))
                        mean_matrix = mfcc_feat.mean(0)
                        feature = (mean_matrix, covariance, i)
                        pickle.dump(feature, f)
                    except Exception as e: 
                        print(f"Error processing {file} in {folder}: {str(e)}")

    def extract_hmm_features(self, file_path):
        """Extract HMM-based features from an audio file."""
        rate, sig = wav.read(file_path)
        mfcc_feat = mfcc(sig, rate, winlen=0.020, appendEnergy=False)

        # Use the pre-trained HMM model to extract HMM-based features
        hmm_features = self.hmm_model.predict(mfcc_feat)
        return hmm_features