import numpy as np
import operator
import pickle
import random

class KNNClassifier:
    def __init__(self, k=5):
        self.k = k
        self.training_set = []
        self.test_set = []

    def distance(self, instance1, instance2):
        """Calculate distance between two instances."""
        mm1, cm1, hmm1 = instance1[0], instance1[1], instance1[2]
        mm2, cm2, hmm2 = instance2[0], instance2[1], instance2[2]

        # Calculate distance based on MFCC features
        mfcc_distance = np.trace(np.dot(np.linalg.inv(cm2), cm1))
        mfcc_distance += np.dot(np.dot((mm2-mm1).transpose(), np.linalg.inv(cm2)), mm2-mm1)
        mfcc_distance += np.log(np.linalg.det(cm2)) - np.log(np.linalg.det(cm1))

        # Calculate distance based on HMM-based features
        hmm_distance = np.sum((hmm1 - hmm2) ** 2)

        # Combine MFCC and HMM-based distances
        total_distance = mfcc_distance + hmm_distance - self.k
        return total_distance

    def load_dataset(self, filename, split=0.68):
        """Load dataset and split into training and test sets."""
        dataset = []
        with open(filename, 'rb') as f:
            while True:
                try:
                    dataset.append(pickle.load(f))
                except EOFError:
                    break

        for x in dataset:
            if random.random() < split:
                self.training_set.append(x)
            else:
                self.test_set.append(x)

        return len(self.training_set), len(self.test_set)

    def get_neighbors(self, training_set, instance):
        """Find k nearest neighbors for an instance."""
        distances = []
        for x in range(len(training_set)):
            dist = self.distance(training_set[x], instance) + self.distance(instance, training_set[x])
            distances.append((training_set[x][2], dist))

        # Sort by distance
        distances.sort(key=operator.itemgetter(1))
        neighbors = [distances[x][0] for x in range(self.k)]
        return neighbors

    def nearest_class(self, neighbors):
        """Identify the most common class among neighbors."""
        class_votes = {}
        for response in neighbors:
            class_votes[response] = class_votes.get(response, 0) + 1
        sorted_votes = sorted(class_votes.items(), key=operator.itemgetter(1), reverse=True)
        return sorted_votes[0][0]

    def predict(self, instance):
        """Predict the class for a single instance."""
        neighbors = self.get_neighbors(self.training_set, instance)
        return self.nearest_class(neighbors)

    def evaluate(self, test_set=None):
        """Evaluate the model's accuracy."""
        if test_set is None:
            test_set = self.test_set

        predictions = []
        for x in range(len(test_set)):
            predictions.append(self.predict(test_set[x]))

        correct = sum(1 for i in range(len(test_set)) if test_set[i][2] == predictions[i])
        return correct / len(test_set)