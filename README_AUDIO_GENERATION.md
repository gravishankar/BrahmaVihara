# Brahma Vihara Meditation Audio Generation

This directory contains a complete system for generating guided meditation audio for the Brahma Vihara practice using local text-to-speech (TTS) via Chatterbox.

## Overview

**Status:** ✅ All 169 meditation audio files generated successfully

- **Total Files:** 169 MP3 segments
- **Total Size:** 5.4 MB
- **Generation Time:** ~9 minutes (batch) with Apple Silicon acceleration
- **Quality:** Meditative-paced (0.82x speed), normalized volume
- **Cost:** $0 (local processing, no cloud API fees)

## Audio Files

The `audio/` directory contains meditation segments organized by phase:

```
audio/
├── settle_01.mp3 → settle_20.mp3   (20 files) - Initial settling
├── metta_01.mp3 → metta_38.mp3     (38 files) - Loving-kindness
├── karuna_01.mp3 → karuna_31.mp3   (31 files) - Compassion
├── mudita_01.mp3 → mudita_32.mp3   (32 files) - Sympathetic joy
├── upekkha_01.mp3 → upekkha_33.mp3 (33 files) - Equanimity
└── close_01.mp3 → close_15.mp3     (15 files) - Closing
```

## Using the Meditation App

Open `brahma-vihara-meditation-app.html` in a web browser to play the guided meditation. The app will play all segments sequentially with proper timing and controls.

## Regenerating Audio Files

### Prerequisites

1. **Python Virtual Environment**
   ```bash
   # Already set up at:
   /Users/gravisha/venvs/chatterbox
   ```

2. **Required Packages** (already installed)
   - torch
   - torchaudio
   - torchvision
   - chatterbox-tts
   - ffmpeg

### Generate All Files

```bash
cd /Users/gravisha/projects/BhavanaSociety/BrahmaVihara

source /Users/gravisha/venvs/chatterbox/bin/activate

python3 brahma_vihara_chatterbox_gen.py
```

### Generate Specific Phases

Generate only one meditation phase:

```bash
# Generate only the metta (loving-kindness) phase
python3 brahma_vihara_chatterbox_gen.py --phase metta

# Valid phases: settle, metta, karuna, mudita, upekkha, close
```

### Generate Test Files

Generate first 5 files only (for testing quality):

```bash
python3 brahma_vihara_chatterbox_gen.py --test
```

### Adjust Speech Speed

Modify the meditation pacing (slower = more spacious):

```bash
# Slower (0.70x) - very spacious
python3 brahma_vihara_chatterbox_gen.py --speed 0.70

# Default (0.82x) - meditative
python3 brahma_vihara_chatterbox_gen.py --speed 0.82

# Faster (0.90x) - more energetic
python3 brahma_vihara_chatterbox_gen.py --speed 0.90
```

### Other Options

```bash
# Preview without generating (dry-run)
python3 brahma_vihara_chatterbox_gen.py --dry-run

# Regenerate existing files (force overwrite)
python3 brahma_vihara_chatterbox_gen.py --force

# Force + adjust speed
python3 brahma_vihara_chatterbox_gen.py --force --speed 0.85
```

## Technical Details

### Audio Generation Pipeline

1. **Text-to-Speech:** Chatterbox TTS (local, no cloud API)
2. **Voice:** Single pretrained voice (warm, calm, suitable for meditation)
3. **Processing Pipeline:**
   - Generate WAV file from text using Chatterbox
   - Slow down speech to 0.82x speed (spacious, meditative pace)
   - Normalize loudness to -18 LUFS (consistent volume)
   - Convert to MP3 (high quality, 44.1kHz, 192kbps)

### Performance

- **Device:** Apple Silicon (MPS acceleration)
- **Speed:** ~3.2 seconds per file average
- **Total Time:** ~9 minutes for 169 files
- **Fallback:** Automatic CPU fallback if MPS unavailable

### File Characteristics

- **Format:** MP3 (MPEG Layer III)
- **Sample Rate:** 24 kHz (audio generated), converted to 44.1kHz
- **Bitrate:** 192 kbps (high quality)
- **Size:** 25-50 KB per file (varies by text length)

## Troubleshooting

### Model Download Issues

On first run, Chatterbox downloads pretrained models (~500MB). If downloads are slow:

```bash
# Set cache directory and disable experimental transfer mode
source /Users/gravisha/venvs/chatterbox/bin/activate

HF_HOME=/tmp/chatterbox-cache/hf \
NUMBA_CACHE_DIR=/tmp/chatterbox-cache/numba \
HF_HUB_DISABLE_XET=1 \
python3 brahma_vihara_chatterbox_gen.py
```

### Generation Failures

If files fail to generate:

```bash
# Force regenerate failed files
python3 brahma_vihara_chatterbox_gen.py --force

# Or regenerate specific phase
python3 brahma_vihara_chatterbox_gen.py --phase metta --force
```

### Quality Issues

If audio quality needs adjustment, regenerate with different settings:

```bash
# More volume normalization (louder)
# Edit LOUDNESS_TARGET in brahma_vihara_chatterbox_gen.py to -16 LUFS

# Different speed (slower = more spacious)
python3 brahma_vihara_chatterbox_gen.py --speed 0.75 --force
```

## Architecture

### Files Included

- **brahma_vihara_chatterbox_gen.py** - Main audio generator script
- **brahma-vihara-meditation-app.html** - Web app to play meditation
- **audio/** - Generated MP3 files
- **README_AUDIO_GENERATION.md** - This file

### Key Script Features

- ✅ Monkeypatch for Chatterbox watermarking compatibility
- ✅ Apple Silicon MPS acceleration
- ✅ Automatic file skipping (only regenerate missing files)
- ✅ Batch processing with progress tracking
- ✅ Graceful error handling
- ✅ Configurable speed and processing parameters
- ✅ Dry-run mode for previewing without generation

## Future Enhancements

Possible improvements for future versions:

1. **Alternative Voices** - Explore other TTS models (Coqui, glow-tts)
2. **Background Audio** - Add ambient sound (bells, nature sounds)
3. **Silence Padding** - Add customizable silence between segments
4. **Audio Stitching** - Concatenate into single long meditation file
5. **Distribution** - Package as offline downloadable files

## Notes

- **Cost:** Zero cloud API fees (all processing local)
- **Privacy:** No audio sent to external servers
- **Customization:** Can regenerate with any parameters at any time
- **Portability:** Works on any macOS with Apple Silicon
- **Dependency:** Requires Python 3.11+ and ffmpeg

## Support

For issues or questions:

1. Check the **Troubleshooting** section above
2. Verify virtual environment is activated
3. Ensure ffmpeg is installed: `which ffmpeg`
4. Run with `--dry-run` to test without generation

---

**Generated:** April 28, 2026
**System:** Apple Silicon (M-series) macOS
**TTS Engine:** Chatterbox (local, CPU/MPS)
