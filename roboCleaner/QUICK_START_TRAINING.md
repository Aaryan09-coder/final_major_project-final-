# Quick Start: Train Grip Classifier

## 🚀 Fast Training (3 Steps)

### Step 1: Install Dependencies
```bash
pip install scikit-learn joblib
```

### Step 2: Train Model
```bash
cd roboCleaner
python ml_model/train_grip_classifier.py
```

### Step 3: Done!
The model is automatically saved and will be used by `PoseController`.

---

## 📊 What You'll See

```
Loading fist.json...
  Loaded 1234 samples with label '0'
Loading palm.json...
  Loaded 1234 samples with label '1'

Training Random Forest Classifier...
Accuracy: 0.9234 (92.34%)

✓ Model saved to: ml_model/grip_models/grip_classifier.pkl
```

---

## ✅ Verification

After training, run your controller:
```bash
python run_full_system.py
```

You should see:
```
✓ Using trained grip classifier for better accuracy
```

---

## 📁 Files Created

- `ml_model/grip_models/grip_classifier.pkl` - Trained model
- `ml_model/grip_models/model_metadata.json` - Model info

---

## 🔧 Troubleshooting

**"No module named 'sklearn'"**
→ `pip install scikit-learn`

**"Model not found"**
→ Make sure you ran training script

**"Low accuracy"**
→ Add more samples to `fist_data/fist.json` and `palm.json`

