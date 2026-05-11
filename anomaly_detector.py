import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import logging

logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.is_trained = False
        self.training_data = []

    def add_to_training(self, log_entry: dict):
        """Collects features for training."""
        # Simple features: length of message, number of special characters, etc.
        msg = log_entry.get("message", "")
        features = [
            len(msg),
            msg.count("{") + msg.count("[") + msg.count("("),
            len(re.findall(r'\d+', msg)), # count of digit sequences
            1 if log_entry.get("level") in ["ERROR", "CRITICAL"] else 0
        ]
        self.training_data.append(features)
        
        # Train once we have enough data
        if len(self.training_data) >= 100 and not self.is_trained:
            self.train()

    def train(self):
        logger.info("Training Anomaly Detection model...")
        X = np.array(self.training_data)
        self.model.fit(X)
        self.is_trained = True
        logger.info("Model trained successfully.")

    def is_anomaly(self, log_entry: dict) -> bool:
        """Predicts if a log entry is an anomaly."""
        # Always flag ERRORs as anomalies
        if log_entry.get("level") in ["ERROR", "CRITICAL"]:
            return True

        if not self.is_trained:
            return False

        msg = log_entry.get("message", "")
        features = [[
            len(msg),
            msg.count("{") + msg.count("[") + msg.count("("),
            len(re.findall(r'\d+', msg)),
            0 # Not an error
        ]]
        
        prediction = self.model.predict(features)
        return prediction[0] == -1 # IsolationForest returns -1 for anomalies
