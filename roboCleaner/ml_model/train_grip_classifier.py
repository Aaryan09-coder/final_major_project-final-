"""
Train Grip Classifier Model
Uses MediaPipe hand landmarks from fist_data/fist.json and palm.json
to train a classifier that distinguishes between fist (closed) and palm (open)
"""
import json
import numpy as np
import os
import sys
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def load_landmark_data(json_file_path, label):
    """
    Load MediaPipe hand landmarks from JSON file
    
    Args:
        json_file_path: Path to JSON file (fist.json or palm.json)
        label: Label for this data (0 for fist/closed, 1 for palm/open)
    
    Returns:
        list: List of feature vectors (flattened landmarks)
        list: List of labels
    """
    features = []
    labels = []
    
    print(f"Loading {json_file_path}...")
    
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    count = 0
    for sample_id, sample_data in data.items():
        if 'landmarks' in sample_data and len(sample_data['landmarks']) > 0:
            # Get first hand landmarks (MediaPipe format: 21 points with x, y)
            landmarks = sample_data['landmarks'][0]
            
            if len(landmarks) == 21:  # MediaPipe has 21 hand landmarks
                # Flatten landmarks: [x1, y1, x2, y2, ..., x21, y21] = 42 features
                feature_vector = []
                for point in landmarks:
                    if len(point) >= 2:
                        feature_vector.extend([point[0], point[1]])
                
                if len(feature_vector) == 42:  # 21 points * 2 coordinates
                    features.append(feature_vector)
                    labels.append(label)
                    count += 1
    
    print(f"  Loaded {count} samples with label '{label}'")
    return features, labels

def extract_advanced_features(landmarks):
    """
    Extract advanced features from MediaPipe landmarks
    These features are more robust than raw coordinates
    
    Args:
        landmarks: List of 21 landmark points [[x1, y1], [x2, y2], ...]
    
    Returns:
        list: Advanced feature vector
    """
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
    
    # 7. Hand area (approximate using convex hull or bounding box)
    # Simple: use spread of all points
    all_x = [p[0] for p in points]
    all_y = [p[1] for p in points]
    hand_area = (max(all_x) - min(all_x)) * (max(all_y) - min(all_y))
    features.append(hand_area)
    
    # 8. Normalized coordinates (relative to wrist)
    for tip in tips:
        rel_x = tip[0] - wrist[0]
        rel_y = tip[1] - wrist[1]
        features.extend([rel_x, rel_y])
    
    return features

def load_data_with_advanced_features(fist_json_path, palm_json_path):
    """
    Load data and extract advanced features
    
    Returns:
        X: Feature matrix
        y: Label vector (0=fist, 1=palm)
    """
    # Load raw landmarks
    fist_features, fist_labels = load_landmark_data(fist_json_path, label=0)  # 0 = closed/fist
    palm_features, palm_labels = load_landmark_data(palm_json_path, label=1)  # 1 = open/palm
    
    print(f"\nTotal samples: {len(fist_features)} fist + {len(palm_features)} palm = {len(fist_features) + len(palm_features)}")
    
    # Convert to advanced features
    print("\nExtracting advanced features...")
    advanced_features = []
    advanced_labels = []
    
    # Process fist data
    for landmarks_flat in fist_features:
        # Reshape: [x1, y1, x2, y2, ...] -> [[x1, y1], [x2, y2], ...]
        landmarks = [[landmarks_flat[i], landmarks_flat[i+1]] for i in range(0, len(landmarks_flat), 2)]
        features = extract_advanced_features(landmarks)
        if features:
            advanced_features.append(features)
            advanced_labels.append(0)
    
    # Process palm data
    for landmarks_flat in palm_features:
        landmarks = [[landmarks_flat[i], landmarks_flat[i+1]] for i in range(0, len(landmarks_flat), 2)]
        features = extract_advanced_features(landmarks)
        if features:
            advanced_features.append(features)
            advanced_labels.append(1)
    
    print(f"Extracted {len(advanced_features)} feature vectors")
    print(f"Feature vector size: {len(advanced_features[0]) if advanced_features else 0}")
    
    return np.array(advanced_features), np.array(advanced_labels)

def train_model(X, y, model_type='random_forest'):
    """
    Train grip classification model
    
    Args:
        X: Feature matrix
        y: Label vector
        model_type: 'random_forest' or 'svm'
    
    Returns:
        Trained model
    """
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Train model
    if model_type == 'random_forest':
        print("\nTraining Random Forest Classifier...")
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
    elif model_type == 'svm':
        print("\nTraining SVM Classifier...")
        model = SVC(
            kernel='rbf',
            C=1.0,
            gamma='scale',
            probability=True,
            random_state=42
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n{'='*60}")
    print(f"Model Performance")
    print(f"{'='*60}")
    print(f"Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Fist (Closed)', 'Palm (Open)']))
    print(f"\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print(f"{'='*60}\n")
    
    return model

def main():
    """Main training function"""
    print("="*60)
    print("Grip Classifier Training")
    print("="*60)
    
    # Paths to data files
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    fist_data_dir = project_root / "fist_data"
    
    fist_json = fist_data_dir / "fist.json"
    palm_json = fist_data_dir / "palm.json"
    
    # Check if files exist
    if not fist_json.exists():
        print(f"ERROR: {fist_json} not found!")
        return
    
    if not palm_json.exists():
        print(f"ERROR: {palm_json} not found!")
        return
    
    # Load and prepare data
    X, y = load_data_with_advanced_features(fist_json, palm_json)
    
    if len(X) == 0:
        print("ERROR: No valid data loaded!")
        return
    
    # Train model
    print("\n" + "="*60)
    print("Training Models")
    print("="*60)
    
    # Try both models and pick the best
    rf_model = train_model(X, y, model_type='random_forest')
    svm_model = train_model(X, y, model_type='svm')
    
    # Compare and save best model
    rf_pred = rf_model.predict(X)
    svm_pred = svm_model.predict(X)
    
    rf_acc = accuracy_score(y, rf_pred)
    svm_acc = accuracy_score(y, svm_pred)
    
    if rf_acc >= svm_acc:
        best_model = rf_model
        model_name = "random_forest"
        print(f"\n✓ Random Forest selected (accuracy: {rf_acc:.4f})")
    else:
        best_model = svm_model
        model_name = "svm"
        print(f"\n✓ SVM selected (accuracy: {svm_acc:.4f})")
    
    # Save model
    model_dir = script_dir / "grip_models"
    model_dir.mkdir(exist_ok=True)
    
    model_path = model_dir / "grip_classifier.pkl"
    joblib.dump(best_model, model_path)
    print(f"\n✓ Model saved to: {model_path}")
    
    # Save metadata
    metadata = {
        "model_type": model_name,
        "feature_count": X.shape[1],
        "training_samples": len(X),
        "fist_samples": int(np.sum(y == 0)),
        "palm_samples": int(np.sum(y == 1)),
        "accuracy": float(rf_acc if model_name == "random_forest" else svm_acc)
    }
    
    import json as json_lib
    metadata_path = model_dir / "model_metadata.json"
    with open(metadata_path, 'w') as f:
        json_lib.dump(metadata, f, indent=2)
    print(f"✓ Metadata saved to: {metadata_path}")
    
    print("\n" + "="*60)
    print("Training Complete!")
    print("="*60)
    print(f"\nModel ready for use in PoseController")
    print(f"Model path: {model_path}")

if __name__ == "__main__":
    main()

