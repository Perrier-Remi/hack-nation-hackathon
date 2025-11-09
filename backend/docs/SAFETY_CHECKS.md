# Safety & Ethics Checking Guide

## Overview

The Safety Checker analyzes video content for safety and ethical concerns using Google's Gemini AI. It provides comprehensive analysis across three key areas:

1. **NSFW/Violence Detection** - Visual content analysis
2. **Bias/Stereotypes** - Language and messaging analysis
3. **Misleading Claims** - Truthfulness and verifiability checks

## How It Works

### Architecture

```
Video Hash
    ↓
Load Cached Transcript
    ↓
Load Keyframes from Scenes
    ↓
SafetyChecker Analysis
    ├─ NSFW/Violence (images)
    ├─ Bias/Stereotypes (text)
    └─ Misleading Claims (keywords + AI)
    ↓
Generate Safety Report
    ↓
Cache Results
```

### Scoring System

Each check returns:
- **Score**: 0-100 (where 100 is completely safe)
- **Flag**: `safe`, `warning`, or `unsafe`
- **Details**: Explanation of findings
- **Issues**: Specific problems identified

**Overall Severity Levels:**
- **Safe** (≥80): Content passes all checks
- **Warning** (60-79): Some concerns identified, review recommended
- **Unsafe** (<60): Significant issues detected

## API Usage

### Endpoint

```
POST /safety-check
```

### Request Body

```json
{
  "video_hash": "abc123def456"
}
```

The video hash must correspond to a video that has:
1. Been transcribed (transcript exists in `uploads/transcripts/`)
2. Been processed for scenes (keyframes exist in `uploads/frames/`)

### Response Format

```json
{
  "success": true,
  "video_hash": "abc123def456",
  "overall_score": 85.0,
  "severity": "safe",
  "nsfw_violence": {
    "score": 95,
    "flag": "safe",
    "details": "No NSFW or violent content detected",
    "frames_analyzed": 10,
    "issues_found": []
  },
  "bias_stereotypes": {
    "score": 80,
    "flag": "safe",
    "details": "Language is inclusive and unbiased",
    "issues_found": []
  },
  "misleading_claims": {
    "score": 90,
    "flag": "safe",
    "details": "No misleading claims detected",
    "keywords_found": [],
    "misleading_claims": []
  },
  "cached": false,
  "checked_at": "2025-11-09T12:00:00Z"
}
```

## Analysis Methods

### 1. NSFW/Violence Detection

**What it checks:**
- Nudity or sexual content
- Violence or gore
- Disturbing imagery
- Dangerous activities

**Method:**
- Samples up to 10 representative keyframes
- Uploads images to Gemini Vision API
- AI analyzes visual content for safety concerns

**Score interpretation:**
- 90-100: Completely safe
- 70-89: Minor concerns
- <70: Significant issues

### 2. Bias/Stereotypes

**What it checks:**
- Gender stereotypes
- Racial/ethnic stereotypes
- Ageism
- Ableism (disability bias)
- Body shaming
- Socioeconomic bias
- Cultural insensitivity
- Heteronormative assumptions

**Method:**
- Analyzes transcript text using Gemini
- Checks for non-inclusive language
- Identifies discriminatory messaging

**Score interpretation:**
- 90-100: Highly inclusive
- 70-89: Mostly inclusive with minor issues
- <70: Contains biased language

### 3. Misleading Claims

**What it checks:**
- Unverifiable health/medical claims
- Exaggerated effectiveness claims
- False guarantees
- Misleading statistics
- Deceptive omissions
- "Too good to be true" offers

**Method:**
1. **Rule-based keyword detection** (first pass)
   - Scans for misleading keywords: "guaranteed", "cure", "miracle", etc.
2. **AI verification** (if keywords found)
   - Gemini analyzes context
   - Determines if claims are actually misleading

**Flagged keywords:**
- guaranteed, guarantee
- cure, cures
- miracle, miraculous
- 100%, never fails, always works
- proven, scientifically proven
- FDA approved, clinically tested
- instant results, overnight
- secret formula
- doctors hate, one weird trick

**Score interpretation:**
- 90-100: Truthful and verifiable
- 70-89: Some questionable claims
- <70: Contains misleading information

## Caching

Safety reports are automatically cached to:
```
uploads/safety/{video_hash}_safety_report.json
```

**Cache behavior:**
- First check: Full analysis, saves results
- Subsequent checks: Returns cached results instantly
- Cache key: Video hash (same video = same report)

**To force re-analysis:**
```bash
rm uploads/safety/{video_hash}_safety_report.json
```

## Testing

Run the test script to verify safety checking:

```bash
cd backend
python3 test_safety_checker.py
```

**Requirements:**
- Video must have been transcribed first
- Video should have keyframes (scene detection run)
- API key must be configured

## Integration

### With Transcription Pipeline

```python
# 1. Transcribe video
POST /transcript
{
  "video": <video_file>
}

# 2. Check safety (use video hash from upload)
POST /safety-check
{
  "video_hash": "abc123"
}
```

### Programmatic Usage

```python
from analyzers.safety_checker import SafetyChecker

# Create checker
checker = SafetyChecker()

# Run check
result = checker.check_safety(
    transcript="Your ad transcript here...",
    keyframe_paths=["/path/to/frame1.jpg", "/path/to/frame2.jpg"],
    max_frames=10
)

# Check results
if result['severity'] == 'safe':
    print("Content is safe!")
elif result['severity'] == 'warning':
    print(f"Warning: {result['bias_stereotypes']['details']}")
else:
    print("Content has safety concerns!")
```

## Best Practices

### 1. Always Transcribe First
Safety checks require a transcript. Run `/transcript` endpoint before `/safety-check`.

### 2. Include Keyframes
While not required, keyframes significantly improve NSFW/violence detection accuracy.

### 3. Review Warnings
`warning` severity doesn't mean automatic rejection. Review the details to understand specific concerns.

### 4. Consider Context
Gemini provides context-aware analysis. What might be inappropriate in one context could be acceptable in another (e.g., medical ads discussing health conditions).

### 5. Use as a Tool, Not a Judge
Safety checks assist human review but shouldn't replace it entirely for critical decisions.

## Troubleshooting

### "Transcript not found"
**Solution:** Run `/transcript` endpoint first to generate transcript.

### "No keyframes found"
**Issue:** Scene detection hasn't been run.
**Solution:** Process video with `AudioProcessor` which generates keyframes automatically.

### Low scores with safe content
**Possible causes:**
- Ambiguous language that AI misinterprets
- False positive keyword detection
- Technical/medical terminology flagged incorrectly

**Solution:** Review the details field for context. Consider if legitimate use case.

### Analysis errors
**Check:**
1. API key is valid and has quota
2. Images exist and are readable
3. Transcript is not empty

## Configuration

Edit `config.py` to customize:

```python
# Severity thresholds
SAFETY_SEVERITY_THRESHOLDS = {
    'safe': 80,     # Adjust as needed
    'warning': 60,
    'unsafe': 0
}

# Add/remove misleading keywords
MISLEADING_KEYWORDS = [
    "guaranteed",
    "cure",
    # ... your keywords
]
```

## Privacy & Security

- Images are temporarily uploaded to Gemini for analysis
- Images are deleted from Gemini after analysis
- Transcripts are not sent externally (already on disk)
- Results are cached locally only
- No data is shared with third parties

## Performance

**Typical analysis time:**
- With keyframes: 30-60 seconds
- Text only: 10-20 seconds
- Cached result: <1 second

**API costs:**
- Each check = 3 Gemini API calls (one per analysis type)
- Image analysis costs more than text
- Caching significantly reduces costs

## Future Enhancements

Planned improvements:
- Sentiment analysis
- Brand safety categories
- Multi-language support
- Custom keyword lists per advertiser
- Severity level customization
- Automated flagging workflows

---

**Last Updated:** November 2025  
**Version:** 1.0

