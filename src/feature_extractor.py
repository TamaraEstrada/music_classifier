import numpy as np
import scipy.io.wavfile as wav
from python_speech_features import mfcc
import pickle
import os
from hmmlearn import hmm
import requests
import io
from pydub import AudioSegment
import tempfile

class FeatureExtractor:
    def __init__(self, data_directory):
        self.directory = data_directory
        self.n_components = 10  # Number of HMM states
        self.n_mfcc = 13  # Number of MFCC coefficients
        self.hmm_model = None
        self.initialize_hmm_model()
    
    def initialize_hmm_model(self):
        """Initialize HMM model without training."""
        self.hmm_model = hmm.GaussianHMM(
            n_components=self.n_components,
            covariance_type="diag",
            n_iter=100,
            random_state=42
        )


    def download_and_convert_audio(self, preview_url):
        """Download audio from URL and convert to WAV format."""
        try:
            # Download the audio file
            response = requests.get(preview_url)
            if response.status_code != 200:
                print(f"Failed to download audio: {response.status_code}")
                return None

            # Create a temporary file for the downloaded MP3
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
                temp_mp3.write(response.content)
                temp_mp3_path = temp_mp3.name

            # Convert MP3 to WAV
            audio = AudioSegment.from_mp3(temp_mp3_path)
            
            # Create a temporary file for the WAV
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                audio.export(temp_wav.name, format='wav')
                temp_wav_path = temp_wav.name

            # Read the WAV file
            rate, sig = wav.read(temp_wav_path)

            # Clean up temporary files
            os.unlink(temp_mp3_path)
            os.unlink(temp_wav_path)

            return rate, sig
        except Exception as e:
            print(f"Error processing audio from URL: {e}")
            return None, None

    
    def load_mfcc_features(self, file_path):
        """Load MFCC features from the binary file."""
        features = []
        labels = []
        
        with open(file_path, 'rb') as f:
            while True:
                try:
                    data = pickle.load(f)
                    if len(data) == 3:  # Unpack only if data has expected format
                        mean_matrix, covariance, label = data
                        features.append(mean_matrix)  # Use only mean_matrix for HMM
                        labels.append(label)
                except EOFError:
                    break
                except Exception as e:
                    print(f"Error loading feature: {e}")
                    continue
        
        return np.array(features), np.array(labels)

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
                        
                        # Extract MFCC features
                        mfcc_feat = mfcc(sig, rate, winlen=0.020, appendEnergy=False)
                        
                        # Calculate statistical features
                        covariance = np.cov(np.matrix.transpose(mfcc_feat))
                        mean_matrix = mfcc_feat.mean(0)
                        
                        # Save features without HMM at this stage
                        feature = (mean_matrix, covariance, i)
                        pickle.dump(feature, f)
                        
                    except Exception as e:
                        print(f"Error processing {file} in {folder}: {str(e)}")

    def extract_features_for_song(self, preview_url):
        """Extract features from a song preview URL."""
        try:
            # Download and convert the audio
            rate, sig = self.download_and_convert_audio(preview_url)
            if rate is None or sig is None:
                return None

            # Extract MFCC features
            mfcc_feat = mfcc(sig, rate, winlen=0.020, appendEnergy=False)
            
            # Calculate statistical features
            covariance = np.cov(np.matrix.transpose(mfcc_feat))
            mean_matrix = mfcc_feat.mean(0)
            
            # Create default HMM features
            hmm_features = np.zeros(self.n_components)
            
            return mean_matrix, covariance, hmm_features
            
        except Exception as e:
            print(f"Error extracting features from preview URL: {e}")
            return None
        
        
    def preprocess_audio(self, audio_file):
        """Preprocess audio file for feature extraction."""
        try:
            rate, sig = wav.read(audio_file)
            
            # Ensure consistent audio length
            target_length = rate * 30  # 30 seconds
            if len(sig) > target_length:
                sig = sig[:target_length]
            else:
                # Pad with zeros if audio is too short
                sig = np.pad(sig, (0, target_length - len(sig)))
            
            return sig, rate
        except Exception as e:
            print(f"Error preprocessing audio: {e}")
            return None, None