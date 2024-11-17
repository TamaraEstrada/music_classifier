import numpy as np
import scipy.io.wavfile as wav
from python_speech_features import mfcc
import pickle
import os

class FeatureExtractor:
    def __init__(self, data_directory):
        self.directory = data_directory
        
    def extract_features(self, output_file="dataset.dat"):
        """Extract MFCC features from audio files and save to binary file."""
        with open(output_file, "wb") as f:
            for i, folder in enumerate(os.listdir(self.directory), 1):
                if i == 11:  # We have 10 genres
                    break
                    
                folder_path = os.path.join(self.directory, folder)
                print(f"Processing folder: {folder}")
                
                for file in os.listdir(folder_path):
                    try:
                        file_path = os.path.join(folder_path, file)
                        rate, sig = wav.read(file_path)
                        mfcc_feat = mfcc(sig, rate, winlen=0.020, appendEnergy=False)
                        covariance = np.cov(np.matrix.transpose(mfcc_feat))
                        mean_matrix = mfcc_feat.mean(0)
                        feature = (mean_matrix, covariance, i)
                        pickle.dump(feature, f)
                    except Exception as e:
                        print(f"Error processing {file} in {folder}: {str(e)}")
