# AI Image Detection Guide

## Overview

TrustCard uses the `umm-maybe/AI-image-detector` model from Hugging Face to detect AI-generated images.

## How It Works

1. **Download Image** - Fetches image from Instagram URL
2. **Preprocess** - Converts to RGB, resizes if needed
3. **Run Inference** - Feeds image through neural network
4. **Interpret Results** - Converts model output to confidence score

## Model Details

- **Model:** umm-maybe/AI-image-detector
- **Source:** Hugging Face Transformers
- **Type:** Image classification
- **Output:** Binary (AI-generated vs Real)
- **Threshold:** 0.5 confidence

## Performance

### First Run (Cold Start)
- Model download: ~2GB
- Model loading: 10-30 seconds
- First inference: 5-10 seconds

### Subsequent Runs (Warm)
- Model loading: <2 seconds (cached)
- Inference: 0.5-2 seconds per image

### GPU vs CPU
- **GPU:** 0.5-1 second per image
- **CPU:** 2-5 seconds per image

## Confidence Interpretation

| Confidence | Meaning |
|------------|---------|
| 90-100% | Very confident in classification |
| 70-89% | Confident |
| 50-69% | Somewhat confident |
| 0-49% | Low confidence |

## Multiple Images

For posts with multiple images (carousels):
- Each image analyzed separately
- Overall assessment: ANY AI-generated = flagged
- Average confidence calculated

## Limitations

### What It Can Detect
✅ AI-generated images from:
- Midjourney
- DALL-E
- Stable Diffusion
- Other text-to-image models

### What It Cannot Detect
❌ Deepfakes (covered in Step 8)
❌ Photo manipulations/edits
❌ Screenshots of AI images
❌ Compressed/degraded images may be less accurate

## Testing

### Test Locally
```bash
python test_ai_detection.py
```

### Test via API
```bash
python test_with_ai_detection.py
```

## Troubleshooting

### "CUDA out of memory"
- Model trying to use GPU without enough VRAM
- Solution: Will automatically fallback to CPU

### "Model download failed"
- Network issue downloading from Hugging Face
- Solution: Check internet connection, try again

### "Inference very slow"
- Running on CPU (no GPU available)
- Solution: Normal for CPU, consider GPU for production

## Trust Score Impact

AI-generated content affects the trust score:
- **No AI detected:** No penalty (score remains 100)
- **AI detected with low confidence (50-70%):** -15 to -21 points
- **AI detected with high confidence (70-90%):** -21 to -27 points
- **AI detected with very high confidence (90-100%):** -27 to -30 points

### Calculation
```python
if ai_detected:
    penalty = confidence * 30
    trust_score -= penalty
```

### Examples
- Real photo (confidence 95%): Score = 100 (no penalty)
- AI image (confidence 60%): Score = 82 (penalty: -18)
- AI image (confidence 90%): Score = 73 (penalty: -27)
- AI image (confidence 100%): Score = 70 (penalty: -30)

## API Response Format

```json
{
  "ai_detection": {
    "status": "completed",
    "overall": {
      "overall_ai_detected": false,
      "confidence": 0.92,
      "total_images": 1,
      "ai_images": 0,
      "real_images": 1,
      "uncertain_images": 0,
      "assessment": "All images appear to be authentic photographs"
    },
    "individual_results": [
      {
        "is_ai_generated": false,
        "confidence": 0.92,
        "ai_score": 0.08,
        "real_score": 0.92,
        "inference_time": 1.23,
        "model": "umm-maybe/AI-image-detector",
        "device": "CPU",
        "image_url": "https://...",
        "image_size": "1080x1350"
      }
    ],
    "model": "umm-maybe/AI-image-detector"
  }
}
```

## Integration in Analysis Pipeline

1. **Instagram Extraction** → Provides image URLs
2. **AI Detection** → Analyzes each image
3. **Trust Score** → Applies penalty if AI detected
4. **Results** → Returned to user via API

## Future Improvements

- Batch processing for faster multi-image analysis
- Model quantization for faster inference
- Custom fine-tuned model for specific AI generators
- Support for more image formats
- Ensemble models for better accuracy
- Explainability: Show which parts of image look AI-generated
