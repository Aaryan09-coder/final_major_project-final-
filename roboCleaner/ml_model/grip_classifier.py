"""
Grip Classifier
Uses trained model to classify hand gestures as fist (closed) or palm (open)
"""
import numpy as np
import joblib
import json
from pathlib import Path

class GripClassifier:
    """Classify hand gestures using trained model"""
    
    def __init__(self, model_path=None):
        """
        Initialize grip classifier
        
        Args:
            model_path: Path to trained model (.pkl file)
                       If None, tries to load from default location
        """
        if model_path is None:
            # Default path
            script_dir = Path(__file__).parent
            model_path = script_dir / "grip_models" / "grip_classifier.pkl"
        
        self.model_path = Path(model_path)
        self.model = None
        self.metadata = None
        
        if self.model_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                # Load metadata if available
                metadata_path = self.model_path.parent / "model_metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        self.metadata = json.load(f)
                print(f"✓ Loaded grip classifier from {self.model_path}")
            except Exception as e:
                print(f"⚠ Failed to load grip classifier: {e}")
                self.model = None
        else:
            print(f"⚠ Grip classifier model not found at {self.model_path}")
            print(f"  Run train_grip_classifier.py to train a model")
    
    def extract_features(self, landmarks):
        """
        Extract features from MediaPipe hand landmarks
        
        Args:
            landmarks: List of 21 MediaPipe landmark points
                      Format: [[x1, y1], [x2, y2], ..., [x21, y21]]
                      OR MediaPipe landmark object with .landmark attribute
        
        Returns:
            numpy array: Feature vector or None if invalid
        """
        # Handle MediaPipe landmark object
        if hasattr(landmarks, 'landmark'):
            points = []
            for lm in landmarks.landmark:
                points.append([lm.x, lm.y])
            landmarks = points
        
        if len(landmarks) != 21:
            return None
        
        # Convert to numpy array
        points = np.array(landmarks)
        
        # Wrist is landmark 0
        wrist = points[0]
        
        # Finger tips: thumb(4), index(8), middle(12), ring(16), pinky(20)
        tips = [points[4], points[8], points[12], points[16], points[20]]
        
        # Finger MCPs (base of fingers): index(5), middle(9), ring(13), pinky(17)
        mcps = [points[5], points[9], points[13], points[17]]
        
        features = []
        
        # 1. Distances from wrist to each fingertip (5 features)
        for tip in tips:
            dist = np.linalg.norm(tip - wrist)
            features.append(dist)
        
        # 2. Average distance from wrist to fingertips
        avg_tip_dist = np.mean([np.linalg.norm(tip - wrist) for tip in tips])
        features.append(avg_tip_dist)
        
        # 3. Spread between fingertips (hand width)
        tip_x_coords = [tip[0] for tip in tips]
        tip_y_coords = [tip[1] for tip in tips]
        hand_width = max(tip_x_coords) - min(tip_x_coords)
        hand_height = max(tip_y_coords) - min(tip_y_coords)
        features.extend([hand_width, hand_height])
        
        # 4. Distance between thumb tip and index tip (pinch distance)
        thumb_index_dist = np.linalg.norm(tips[0] - tips[1])
        features.append(thumb_index_dist)
        
        # 5. Distance between index and middle tips
        index_middle_dist = np.linalg.norm(tips[1] - tips[2])
        features.append(index_middle_dist)
        
        # 6. Angles between fingers (using MCPs)
        for i in range(len(mcps) - 1):
            vec1 = mcps[i] - wrist
            vec2 = mcps[i+1] - wrist
            # Cosine of angle
            cos_angle = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-6)
            features.append(cos_angle)
        
        # 7. Hand area (approximate using bounding box)
        all_x = [p[0] for p in points]
        all_y = [p[1] for p in points]
        hand_area = (max(all_x) - min(all_x)) * (max(all_y) - min(all_y))
        features.append(hand_area)
        
        # 8. Normalized coordinates (relative to wrist)
        for tip in tips:
            rel_x = tip[0] - wrist[0]
            rel_y = tip[1] - wrist[1]
            features.extend([rel_x, rel_y])
        
        return np.array(features)
    
    def predict(self, landmarks):
        """
        Predict if hand is closed (fist) or open (palm)
        
        Args:
            landmarks: MediaPipe hand landmarks (21 points)
        
        Returns:
            dict with keys:
                - 'is_closed': bool (True for fist, False for palm)
                - 'confidence': float (0-1, confidence in prediction)
                - 'raw_value': float (raw model output)
        """
        if self.model is None:
            return None
        
        features = self.extract_features(landmarks)
        if features is None:
            return None
        
        # Reshape for single sample
        features = features.reshape(1, -1)
        
        # Predict
        prediction = self.model.predict(features)[0]
        probabilities = None
        
        # Get confidence if model supports it
        if hasattr(self.model, 'predict_proba'):
            probabilities = self.model.predict_proba(features)[0]
            confidence = max(probabilities)
        else:
            confidence = 1.0  # Default if no probability available
        
        return {
            'is_closed': bool(prediction == 0),  # 0 = fist/closed, 1 = palm/open
            'confidence': float(confidence),
            'raw_value': float(prediction),
            'probabilities': probabilities.tolist() if probabilities is not None else None
        }
    
    def is_available(self):
        """Check if classifier is loaded and ready"""
        return self.model is not None

