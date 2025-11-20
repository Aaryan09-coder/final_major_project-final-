# Grip Detection Training Guide

## Overview
This guide explains how to train a custom grip classifier using your MediaPipe hand landmark data to improve fist vs palm detection.

## Files Created

1. **`ml_model/train_grip_classifier.py`** - Training script
2. **`ml_model/grip_classifier.py`** - Classifier class for inference
3. **Updated `client/PoseController.py`** - Integrated trained classifier

## Step-by-Step Training

### Step 1: Install Required Dependencies

```bash
pip install scikit-learn joblib numpy
```

### Step 2: Prepare Your Data

Your data files should be in:
- `roboCleaner/fist_data/fist.json` (closed hand/fist samples)
- `roboCleaner/fist_data/palm.json` (open hand/palm samples)

**Data Format:**
Each JSON file should contain MediaPipe hand landmarks in this format:
```json
{
    "sample_id": {
        "bboxes": [[x, y, w, h]],
        "labels": ["fist" or "palm"],
        "landmarks": [[[x1, y1], [x2, y2], ..., [x21, y21]]]
    }
}
```

### Step 3: Run Training

```bash
cd roboCleaner
python ml_model/train_grip_classifier.py
```

**What it does:**
1. Loads landmarks from `fist.json` and `palm.json`
2. Extracts advanced features (distances, angles, spreads)
3. Trains Random Forest and SVM models
4. Selects best model based on accuracy
5. Saves model to `ml_model/grip_models/grip_classifier.pkl`

### Step 4: Verify Training

After training, you should see:
```
✓ Model saved to: ml_model/grip_models/grip_classifier.pkl
✓ Metadata saved to: ml_model/grip_models/model_metadata.json
```

Check the accuracy score - should be > 85% for good results.

### Step 5: Use Trained Model

The `PoseController` will automatically use the trained model if available:

```python
# In PoseController, it will:
# 1. Try trained classifier first (more accurate)
# 2. Fallback to distance-based method if classifier not available
```

## Features Extracted

The classifier uses these features from MediaPipe landmarks:

1. **Distances from wrist to fingertips** (5 features)
2. **Average tip distance** (1 feature)
3. **Hand width/height** (2 features)
4. **Thumb-index distance** (pinch detection)
5. **Index-middle distance**
6. **Finger angles** (using MCP joints)
7. **Hand area** (bounding box)
8. **Normalized tip coordinates** (relative to wrist)

Total: ~25 features per hand

## Model Types

The training script tries both:
- **Random Forest**: Usually better for this task, more robust
- **SVM**: Can be more accurate with good data

The best one is automatically selected and saved.

## Improving Results

### If accuracy is low (< 80%):

1. **More training data**: Collect more samples in `fist.json` and `palm.json`
2. **Balance classes**: Ensure similar number of fist and palm samples
3. **Quality data**: Remove bad samples (occluded hands, wrong angles)
4. **Feature tuning**: Modify `extract_advanced_features()` in `grip_classifier.py`

### If detection is still poor:

1. **Check MediaPipe detection**: Ensure hands are being detected properly
2. **Adjust confidence threshold**: Modify in `PoseController.py`
3. **Add more features**: Extend feature extraction in `grip_classifier.py`

## Testing the Model

After training, test with:

```python
from ml_model.grip_classifier import GripClassifier
import mediapipe as mp

# Initialize
classifier = GripClassifier()

# Get MediaPipe landmarks (from your detection)
# landmarks = ... (MediaPipe hand landmarks)

# Predict
result = classifier.predict(landmarks)
print(f"Is closed: {result['is_closed']}")
print(f"Confidence: {result['confidence']}")
```

## Integration

The trained model is automatically integrated into `PoseController`:
- If model exists: Uses trained classifier (more accurate)
- If model missing: Falls back to distance-based method (current method)

No code changes needed - just train and the system will use it!

## Troubleshooting

**Problem: "Model not found"**
- Solution: Run training script first

**Problem: "Low accuracy"**
- Solution: Add more training data, ensure balanced classes

**Problem: "Still using fallback method"**
- Solution: Check model path, verify model file exists

**Problem: "Import errors"**
- Solution: Install scikit-learn: `pip install scikit-learn joblib`

