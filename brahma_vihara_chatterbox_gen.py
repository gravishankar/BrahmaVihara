#!/usr/bin/env python3
"""
Brahma Vihara Audio Generator — Chatterbox TTS Local Edition
=============================================================
Generates all 169 guided meditation MP3s using local Chatterbox TTS.
One sentence per file, named by phase and index.

Usage:
    python brahma_vihara_chatterbox_gen.py                 # generate all missing
    python brahma_vihara_chatterbox_gen.py --test          # 5 test files only
    python brahma_vihara_chatterbox_gen.py --phase metta   # one phase only
    python brahma_vihara_chatterbox_gen.py --dry-run       # preview, no generation
    python brahma_vihara_chatterbox_gen.py --force         # regenerate all
    python brahma_vihara_chatterbox_gen.py --speed 0.85    # adjust speech speed

Setup:
    1. Activate venv: source /Users/gravisha/venvs/chatterbox/bin/activate
    2. python brahma_vihara_chatterbox_gen.py --test
    3. Listen to test files in audio/ directory
    4. python brahma_vihara_chatterbox_gen.py  (full batch)

Output:
    audio/settle_01.mp3  through  audio/close_15.mp3
    (169 files total, ~10-15MB total)
"""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# MONKEYPATCH: Fix Chatterbox watermarker issue
# ─────────────────────────────────────────────────────────────

def patch_chatterbox():
    """
    Monkeypatch: Replace None PerthImplicitWatermarker with DummyWatermarker.
    The perth.PerthImplicitWatermarker is None in some environments.
    Use DummyWatermarker as fallback.
    """
    try:
        import perth
        if perth.PerthImplicitWatermarker is None:
            print("⚠ Detected perth.PerthImplicitWatermarker is None")
            print("  Using DummyWatermarker as fallback...")
            # Replace with DummyWatermarker
            perth.PerthImplicitWatermarker = perth.DummyWatermarker
            print("  ✓ Watermarker patched successfully")
    except Exception as e:
        print(f"  ⚠ Could not patch watermarker: {e}")

patch_chatterbox()

# Now import Chatterbox TTS (after patching)
try:
    import torchaudio as ta
    import torch
    from chatterbox.tts import ChatterboxTTS
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("  Ensure virtual environment is activated:")
    print("  source /Users/gravisha/venvs/chatterbox/bin/activate")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

OUTPUT_DIR = Path("audio")
MANIFEST = Path("audio_manifest.json")

# Audio processing settings for meditation
SPEECH_SPEED = 0.82  # Slow, spacious pacing (command-line override: --speed)
PADDING_BEFORE = 0.5  # silence before (seconds)
PADDING_AFTER = 0.5   # silence after (seconds)
LOUDNESS_TARGET = -18.0  # LUFS for normalization

# ─────────────────────────────────────────────────────────────
# SEGMENT MANIFEST (all 169 segments)
# ─────────────────────────────────────────────────────────────

SEGMENTS = [
  # ── SETTLING ──────────────────────────────────────────────
  {"phase":"settle","index":1, "filename":"settle_01.mp3","text":"Find a comfortable upright seat."},
  {"phase":"settle","index":2, "filename":"settle_02.mp3","text":"Let the spine be naturally tall."},
  {"phase":"settle","index":3, "filename":"settle_03.mp3","text":"Rest the hands gently in your lap."},
  {"phase":"settle","index":4, "filename":"settle_04.mp3","text":"Close the eyes, or lower the gaze softly toward the floor."},
  {"phase":"settle","index":5, "filename":"settle_05.mp3","text":"Take one slow, natural breath."},
  {"phase":"settle","index":6, "filename":"settle_06.mp3","text":"Not controlling the breath."},
  {"phase":"settle","index":7, "filename":"settle_07.mp3","text":"Simply noticing it."},
  {"phase":"settle","index":8, "filename":"settle_08.mp3","text":"Take another breath."},
  {"phase":"settle","index":9, "filename":"settle_09.mp3","text":"Feel the body soften."},
  {"phase":"settle","index":10,"filename":"settle_10.mp3","text":"And one more."},
  {"phase":"settle","index":11,"filename":"settle_11.mp3","text":"Let the shoulders drop."},
  {"phase":"settle","index":12,"filename":"settle_12.mp3","text":"Let the jaw release."},
  {"phase":"settle","index":13,"filename":"settle_13.mp3","text":"You are arriving."},
  {"phase":"settle","index":14,"filename":"settle_14.mp3","text":"There is nowhere else to be."},
  {"phase":"settle","index":15,"filename":"settle_15.mp3","text":"Silently, set your intention for this practice."},
  {"phase":"settle","index":16,"filename":"settle_16.mp3","text":"I am here to cultivate the four divine abodes."},
  {"phase":"settle","index":17,"filename":"settle_17.mp3","text":"May they become the constant dwelling place of my heart."},
  {"phase":"settle","index":18,"filename":"settle_18.mp3","text":"Simply rest here."},
  {"phase":"settle","index":19,"filename":"settle_19.mp3","text":"Breathing."},
  {"phase":"settle","index":20,"filename":"settle_20.mp3","text":"Settling."},

  # ── METTĀ ─────────────────────────────────────────────────
  {"phase":"metta","index":1, "filename":"metta_01.mp3","text":"We begin with metta — loving-friendliness."},
  {"phase":"metta","index":2, "filename":"metta_02.mp3","text":"The foundation of all four divine abodes."},
  {"phase":"metta","index":3, "filename":"metta_03.mp3","text":"Metta begins with yourself."},
  {"phase":"metta","index":4, "filename":"metta_04.mp3","text":"A heart at war with itself cannot radiate peace outward."},
  {"phase":"metta","index":5, "filename":"metta_05.mp3","text":"Bring your attention gently to your own heart."},
  {"phase":"metta","index":6, "filename":"metta_06.mp3","text":"Notice whatever is there — without judgment."},
  {"phase":"metta","index":7, "filename":"metta_07.mp3","text":"And silently, offer yourself these wishes."},
  {"phase":"metta","index":8, "filename":"metta_08.mp3","text":"May I be gentle."},
  {"phase":"metta","index":9, "filename":"metta_09.mp3","text":"May I be relaxed."},
  {"phase":"metta","index":10,"filename":"metta_10.mp3","text":"May I be happy and peaceful."},
  {"phase":"metta","index":11,"filename":"metta_11.mp3","text":"May I be healthy."},
  {"phase":"metta","index":12,"filename":"metta_12.mp3","text":"May my heart become soft."},
  {"phase":"metta","index":13,"filename":"metta_13.mp3","text":"May my words be pleasing."},
  {"phase":"metta","index":14,"filename":"metta_14.mp3","text":"May my actions be kind."},
  {"phase":"metta","index":15,"filename":"metta_15.mp3","text":"Now bring to mind someone you love."},
  {"phase":"metta","index":16,"filename":"metta_16.mp3","text":"A parent, a dear friend, a teacher."},
  {"phase":"metta","index":17,"filename":"metta_17.mp3","text":"Hold them in your heart with warmth."},
  {"phase":"metta","index":18,"filename":"metta_18.mp3","text":"May you be well, happy, and peaceful."},
  {"phase":"metta","index":19,"filename":"metta_19.mp3","text":"May no harm come to you."},
  {"phase":"metta","index":20,"filename":"metta_20.mp3","text":"May you have patience, courage, and understanding."},
  {"phase":"metta","index":21,"filename":"metta_21.mp3","text":"To meet and overcome the inevitable difficulties of life."},
  {"phase":"metta","index":22,"filename":"metta_22.mp3","text":"Now bring to mind someone neutral."},
  {"phase":"metta","index":23,"filename":"metta_23.mp3","text":"A neighbor, a stranger you see regularly."},
  {"phase":"metta","index":24,"filename":"metta_24.mp3","text":"Extend the same wish to them."},
  {"phase":"metta","index":25,"filename":"metta_25.mp3","text":"No conditions. No history."},
  {"phase":"metta","index":26,"filename":"metta_26.mp3","text":"Simply — may you be well."},
  {"phase":"metta","index":27,"filename":"metta_27.mp3","text":"And now — gently — bring to mind someone difficult."},
  {"phase":"metta","index":28,"filename":"metta_28.mp3","text":"Someone with whom there is friction or pain."},
  {"phase":"metta","index":29,"filename":"metta_29.mp3","text":"You are not condoning harm."},
  {"phase":"metta","index":30,"filename":"metta_30.mp3","text":"You are dissolving the prison of your own enmity."},
  {"phase":"metta","index":31,"filename":"metta_31.mp3","text":"May you also be well, happy, and peaceful."},
  {"phase":"metta","index":32,"filename":"metta_32.mp3","text":"Now let the mind expand."},
  {"phase":"metta","index":33,"filename":"metta_33.mp3","text":"Like a bell whose sound reaches all four directions."},
  {"phase":"metta","index":34,"filename":"metta_34.mp3","text":"May all beings in all ten directions be well, happy, and peaceful."},
  {"phase":"metta","index":35,"filename":"metta_35.mp3","text":"May all beings everywhere be filled with loving-friendliness."},
  {"phase":"metta","index":36,"filename":"metta_36.mp3","text":"Abundant, exalted, and measureless."},
  {"phase":"metta","index":37,"filename":"metta_37.mp3","text":"Rest in this vast wish."},
  {"phase":"metta","index":38,"filename":"metta_38.mp3","text":"The heart open in all directions."},

  # ── KARUṆĀ ────────────────────────────────────────────────
  {"phase":"karuna","index":1, "filename":"karuna_01.mp3","text":"Karuna — compassion."},
  {"phase":"karuna","index":2, "filename":"karuna_02.mp3","text":"This is what metta becomes when it meets suffering."},
  {"phase":"karuna","index":3, "filename":"karuna_03.mp3","text":"Karuna asks us to turn toward pain."},
  {"phase":"karuna","index":4, "filename":"karuna_04.mp3","text":"Not to be consumed by it."},
  {"phase":"karuna","index":5, "filename":"karuna_05.mp3","text":"But to meet it with steadiness and an open heart."},
  {"phase":"karuna","index":6, "filename":"karuna_06.mp3","text":"Begin with yourself."},
  {"phase":"karuna","index":7, "filename":"karuna_07.mp3","text":"With your own struggles, your own wounds."},
  {"phase":"karuna","index":8, "filename":"karuna_08.mp3","text":"May I be free from pain and sorrow."},
  {"phase":"karuna","index":9, "filename":"karuna_09.mp3","text":"May I hold my own struggles with gentleness."},
  {"phase":"karuna","index":10,"filename":"karuna_10.mp3","text":"May I find relief and ease."},
  {"phase":"karuna","index":11,"filename":"karuna_11.mp3","text":"Now bring to mind someone who is suffering right now."},
  {"phase":"karuna","index":12,"filename":"karuna_12.mp3","text":"Someone carrying something heavy."},
  {"phase":"karuna","index":13,"filename":"karuna_13.mp3","text":"Hold them in your heart with steadiness."},
  {"phase":"karuna","index":14,"filename":"karuna_14.mp3","text":"Not helplessness."},
  {"phase":"karuna","index":15,"filename":"karuna_15.mp3","text":"One arm reaching toward them."},
  {"phase":"karuna","index":16,"filename":"karuna_16.mp3","text":"One arm anchored to the tree."},
  {"phase":"karuna","index":17,"filename":"karuna_17.mp3","text":"May you be free from pain and suffering."},
  {"phase":"karuna","index":18,"filename":"karuna_18.mp3","text":"May you be free from mental and physical distress."},
  {"phase":"karuna","index":19,"filename":"karuna_19.mp3","text":"May you find the relief you need."},
  {"phase":"karuna","index":20,"filename":"karuna_20.mp3","text":"Now open this compassion wider."},
  {"phase":"karuna","index":21,"filename":"karuna_21.mp3","text":"Think of all who are suffering in the world right now."},
  {"phase":"karuna","index":22,"filename":"karuna_22.mp3","text":"You cannot fix their suffering."},
  {"phase":"karuna","index":23,"filename":"karuna_23.mp3","text":"But you can hold it without turning away."},
  {"phase":"karuna","index":24,"filename":"karuna_24.mp3","text":"May all beings who suffer in body find relief."},
  {"phase":"karuna","index":25,"filename":"karuna_25.mp3","text":"May all beings who suffer in mind find peace."},
  {"phase":"karuna","index":26,"filename":"karuna_26.mp3","text":"May compassion flow in all directions — without limit, without exclusion."},
  {"phase":"karuna","index":27,"filename":"karuna_27.mp3","text":"Sit quietly for a moment."},
  {"phase":"karuna","index":28,"filename":"karuna_28.mp3","text":"Simply feel the quality of compassion in the body."},
  {"phase":"karuna","index":29,"filename":"karuna_29.mp3","text":"Steady."},
  {"phase":"karuna","index":30,"filename":"karuna_30.mp3","text":"Open."},
  {"phase":"karuna","index":31,"filename":"karuna_31.mp3","text":"Warm."},

  # ── MUDITĀ ────────────────────────────────────────────────
  {"phase":"mudita","index":1, "filename":"mudita_01.mp3","text":"Mudita — sympathetic joy."},
  {"phase":"mudita","index":2, "filename":"mudita_02.mp3","text":"This is metta meeting happiness."},
  {"phase":"mudita","index":3, "filename":"mudita_03.mp3","text":"Genuine delight in the joy of others."},
  {"phase":"mudita","index":4, "filename":"mudita_04.mp3","text":"Without comparison, without envy."},
  {"phase":"mudita","index":5, "filename":"mudita_05.mp3","text":"Their joy is enough."},
  {"phase":"mudita","index":6, "filename":"mudita_06.mp3","text":"We need not possess it to celebrate it."},
  {"phase":"mudita","index":7, "filename":"mudita_07.mp3","text":"Begin with a moment of your own happiness."},
  {"phase":"mudita","index":8, "filename":"mudita_08.mp3","text":"Something simple."},
  {"phase":"mudita","index":9, "filename":"mudita_09.mp3","text":"A good conversation."},
  {"phase":"mudita","index":10,"filename":"mudita_10.mp3","text":"Morning light."},
  {"phase":"mudita","index":11,"filename":"mudita_11.mp3","text":"A kindness received."},
  {"phase":"mudita","index":12,"filename":"mudita_12.mp3","text":"Let yourself feel it."},
  {"phase":"mudita","index":13,"filename":"mudita_13.mp3","text":"Without rushing past it."},
  {"phase":"mudita","index":14,"filename":"mudita_14.mp3","text":"May my happiness grow and continue."},
  {"phase":"mudita","index":15,"filename":"mudita_15.mp3","text":"May joy arise easily in my heart."},
  {"phase":"mudita","index":16,"filename":"mudita_16.mp3","text":"Now bring to mind someone whose life is going well."},
  {"phase":"mudita","index":17,"filename":"mudita_17.mp3","text":"Someone flourishing."},
  {"phase":"mudita","index":18,"filename":"mudita_18.mp3","text":"Notice any subtle resistance."},
  {"phase":"mudita","index":19,"filename":"mudita_19.mp3","text":"Any comparison or wish that you had what they have."},
  {"phase":"mudita","index":20,"filename":"mudita_20.mp3","text":"This is natural. Simply notice it, and return."},
  {"phase":"mudita","index":21,"filename":"mudita_21.mp3","text":"Their joy is complete in itself."},
  {"phase":"mudita","index":22,"filename":"mudita_22.mp3","text":"I need not possess it to celebrate it."},
  {"phase":"mudita","index":23,"filename":"mudita_23.mp3","text":"May your happiness continue and grow."},
  {"phase":"mudita","index":24,"filename":"mudita_24.mp3","text":"May your joy be lasting and deep."},
  {"phase":"mudita","index":25,"filename":"mudita_25.mp3","text":"I rejoice in your good fortune — may it increase."},
  {"phase":"mudita","index":26,"filename":"mudita_26.mp3","text":"May you not be separated from the happiness you have found."},
  {"phase":"mudita","index":27,"filename":"mudita_27.mp3","text":"Now extend this rejoicing to all beings who are happy."},
  {"phase":"mudita","index":28,"filename":"mudita_28.mp3","text":"May all beings who are happy continue in their happiness."},
  {"phase":"mudita","index":29,"filename":"mudita_29.mp3","text":"May joy abound in all directions — without limit."},
  {"phase":"mudita","index":30,"filename":"mudita_30.mp3","text":"Rest in this quality."},
  {"phase":"mudita","index":31,"filename":"mudita_31.mp3","text":"Let it be light."},
  {"phase":"mudita","index":32,"filename":"mudita_32.mp3","text":"Let it be warm."},

  # ── UPEKKHĀ ───────────────────────────────────────────────
  {"phase":"upekkha","index":1, "filename":"upekkha_01.mp3","text":"Upekkha — equanimity."},
  {"phase":"upekkha","index":2, "filename":"upekkha_02.mp3","text":"The balancing factor."},
  {"phase":"upekkha","index":3, "filename":"upekkha_03.mp3","text":"The crown of the four abodes."},
  {"phase":"upekkha","index":4, "filename":"upekkha_04.mp3","text":"Equanimity is not indifference."},
  {"phase":"upekkha","index":5, "filename":"upekkha_05.mp3","text":"It is stability inside caring."},
  {"phase":"upekkha","index":6, "filename":"upekkha_06.mp3","text":"The mind like a clear sky."},
  {"phase":"upekkha","index":7, "filename":"upekkha_07.mp3","text":"Through which everything passes."},
  {"phase":"upekkha","index":8, "filename":"upekkha_08.mp3","text":"Which nothing disturbs."},
  {"phase":"upekkha","index":9, "filename":"upekkha_09.mp3","text":"Take five slow breaths."},
  {"phase":"upekkha","index":10,"filename":"upekkha_10.mp3","text":"With each breath, feel the weight of the body."},
  {"phase":"upekkha","index":11,"filename":"upekkha_11.mp3","text":"Let the mind settle."},
  {"phase":"upekkha","index":12,"filename":"upekkha_12.mp3","text":"You are not reaching toward anything."},
  {"phase":"upekkha","index":13,"filename":"upekkha_13.mp3","text":"You are simply here."},
  {"phase":"upekkha","index":14,"filename":"upekkha_14.mp3","text":"Bring to mind something you have been gripping."},
  {"phase":"upekkha","index":15,"filename":"upekkha_15.mp3","text":"A worry."},
  {"phase":"upekkha","index":16,"filename":"upekkha_16.mp3","text":"A wish that things were different."},
  {"phase":"upekkha","index":17,"filename":"upekkha_17.mp3","text":"Offer it to equanimity."},
  {"phase":"upekkha","index":18,"filename":"upekkha_18.mp3","text":"Not to stop caring — but to hold it lightly."},
  {"phase":"upekkha","index":19,"filename":"upekkha_19.mp3","text":"All beings are the owners of their own karma."},
  {"phase":"upekkha","index":20,"filename":"upekkha_20.mp3","text":"Their happiness and unhappiness depend on their own actions."},
  {"phase":"upekkha","index":21,"filename":"upekkha_21.mp3","text":"I hold you with an open hand and an open heart."},
  {"phase":"upekkha","index":22,"filename":"upekkha_22.mp3","text":"May I not be swayed by gain and loss."},
  {"phase":"upekkha","index":23,"filename":"upekkha_23.mp3","text":"By praise and blame."},
  {"phase":"upekkha","index":24,"filename":"upekkha_24.mp3","text":"By pleasure and pain."},
  {"phase":"upekkha","index":25,"filename":"upekkha_25.mp3","text":"May the mind be spacious."},
  {"phase":"upekkha","index":26,"filename":"upekkha_26.mp3","text":"And the heart be free."},
  {"phase":"upekkha","index":27,"filename":"upekkha_27.mp3","text":"May all beings rest in balance."},
  {"phase":"upekkha","index":28,"filename":"upekkha_28.mp3","text":"Neither grasping nor pushing away."},
  {"phase":"upekkha","index":29,"filename":"upekkha_29.mp3","text":"May all beings everywhere abide in peace."},
  {"phase":"upekkha","index":30,"filename":"upekkha_30.mp3","text":"Simply rest."},
  {"phase":"upekkha","index":31,"filename":"upekkha_31.mp3","text":"The mind open."},
  {"phase":"upekkha","index":32,"filename":"upekkha_32.mp3","text":"Balanced."},
  {"phase":"upekkha","index":33,"filename":"upekkha_33.mp3","text":"Still."},

  # ── CLOSING ───────────────────────────────────────────────
  {"phase":"close","index":1, "filename":"close_01.mp3","text":"We close our practice with the Bhavana Society closing verse."},
  {"phase":"close","index":2, "filename":"close_02.mp3","text":"May all beings be happy and secure."},
  {"phase":"close","index":3, "filename":"close_03.mp3","text":"May all beings have happy minds."},
  {"phase":"close","index":4, "filename":"close_04.mp3","text":"May all beings be free from suffering."},
  {"phase":"close","index":5, "filename":"close_05.mp3","text":"May all beings quickly obtain liberation."},
  {"phase":"close","index":6, "filename":"close_06.mp3","text":"Sit quietly for a moment."},
  {"phase":"close","index":7, "filename":"close_07.mp3","text":"Notice the quality of the mind."},
  {"phase":"close","index":8, "filename":"close_08.mp3","text":"Perhaps softer."},
  {"phase":"close","index":9, "filename":"close_09.mp3","text":"Perhaps wider."},
  {"phase":"close","index":10,"filename":"close_10.mp3","text":"Whatever is present — it is the fruit of sincere effort."},
  {"phase":"close","index":11,"filename":"close_11.mp3","text":"These states should become the mind's constant dwelling-places."},
  {"phase":"close","index":12,"filename":"close_12.mp3","text":"Not merely places of rare visits, soon forgotten."},
  {"phase":"close","index":13,"filename":"close_13.mp3","text":"Take one slow breath."},
  {"phase":"close","index":14,"filename":"close_14.mp3","text":"And when you are ready, gently open the eyes."},
  {"phase":"close","index":15,"filename":"close_15.mp3","text":"Carry whatever softness you have cultivated here into the rest of your day."},
]

# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_device() -> str:
    """Pick best available device: MPS > CPU"""
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"

def generate_wav(model, text: str) -> tuple:
    """Generate WAV audio from text using Chatterbox.
    Returns: (waveform, sample_rate)
    """
    wav = model.generate(text)
    return wav, model.sr

def process_audio_ffmpeg(wav_path: Path, mp3_path: Path, speed: float = 0.82) -> bool:
    """
    Process WAV → MP3 with ffmpeg:
    1. Slow down to meditative pace (speed parameter, e.g., 0.82x)
    2. Normalize loudness and convert to MP3 in one pass
    """
    try:
        # Convert directly: slow down + normalize + MP3 in one command
        cmd_mp3 = [
            "ffmpeg", "-i", str(wav_path),
            "-filter:a", f"atempo={speed},loudnorm=I={LOUDNESS_TARGET}",
            "-codec:a", "libmp3lame",
            "-qscale:a", "2",
            "-y", str(mp3_path)
        ]
        result = subprocess.run(cmd_mp3, capture_output=True, check=True)

        # Cleanup original WAV
        wav_path.unlink(missing_ok=True)

        return True
    except subprocess.CalledProcessError as e:
        print(f"    ✗ ffmpeg error: {e.stderr.decode() if e.stderr else e}")
        return False
    except Exception as e:
        print(f"    ✗ Process error: {e}")
        return False

def generate_audio(model, segment, output_path: Path, dry_run=False) -> bool:
    """Generate one MP3 for a single text segment."""
    if dry_run:
        print(f"    [DRY RUN] Would generate: {output_path.name}  \"{segment['text'][:50]}\"")
        return True

    try:
        # Generate WAV
        wav, sr = generate_wav(model, segment["text"])

        # Save WAV temporarily
        temp_wav = output_path.parent / f"{output_path.stem}_temp.wav"
        ta.save(str(temp_wav), wav, sr)

        # Process to MP3
        if process_audio_ffmpeg(temp_wav, output_path, SPEECH_SPEED):
            return True
        else:
            print(f"    ✗ Failed to process {output_path.name}")
            return False

    except Exception as e:
        print(f"    ✗ ERROR {output_path.name}: {e}")
        return False

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate Brahma Vihara meditation audio with Chatterbox TTS")
    parser.add_argument("--test",       action="store_true", help="Generate 5 test files only")
    parser.add_argument("--phase",      help="Only generate one phase: settle|metta|karuna|mudita|upekkha|close")
    parser.add_argument("--dry-run",    action="store_true", help="Preview without generation")
    parser.add_argument("--force",      action="store_true", help="Regenerate even if file exists")
    parser.add_argument("--speed",      type=float, default=0.82, help="Speech speed (0.5-1.5, default 0.82)")
    args = parser.parse_args()

    # Update global speed if specified
    global SPEECH_SPEED
    SPEECH_SPEED = args.speed

    # Load model
    device = get_device()
    print(f"Loading Chatterbox model on {device}...")
    try:
        model = ChatterboxTTS.from_pretrained(device=device)
        print(f"✓ Model loaded (sample rate: {model.sr} Hz)")
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        sys.exit(1)

    # Filter segments
    segments = SEGMENTS
    if args.test:
        segments = [s for s in segments if s["phase"] == "settle" and s["index"] <= 5]
        print("▸ TEST MODE: First 5 settle segments only")
    elif args.phase:
        segments = [s for s in segments if s["phase"] == args.phase]
        if not segments:
            print(f"✗ Phase '{args.phase}' not found. Valid: settle metta karuna mudita upekkha close")
            sys.exit(1)

    # Summary
    print(f"\nBrahma Vihara Audio Generator — Chatterbox TTS")
    print(f"{'─'*60}")
    print(f"  Segments to generate : {len(segments)}")
    print(f"  Speech speed         : {SPEECH_SPEED}x")
    print(f"  Output directory     : {OUTPUT_DIR}/")
    print(f"  Device               : {device}")
    if args.dry_run:   print(f"  Mode                 : DRY RUN — no generation")
    if args.force:     print(f"  Mode                 : FORCE — regenerating all")
    print()

    if args.dry_run:
        for i, seg in enumerate(segments, 1):
            print(f"  [{i:03d}/{len(segments)}] ▶ {seg['filename']}  \"{seg['text'][:50]}\"")
        return

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Generate
    generated = 0
    skipped = 0
    errors = 0
    start_time = time.time()

    for i, seg in enumerate(segments, 1):
        out_path = OUTPUT_DIR / seg["filename"]

        if out_path.exists() and not args.force:
            print(f"  [{i:03d}/{len(segments)}] ⟳ skip  {seg['filename']}")
            skipped += 1
            continue

        print(f"  [{i:03d}/{len(segments)}] ▶ gen   {seg['filename']}  \"{seg['text'][:45]}\"")
        ok = generate_audio(model, seg, out_path)
        if ok:
            generated += 1
        else:
            errors += 1

    # Summary
    elapsed = time.time() - start_time
    print(f"\n{'─'*60}")
    print(f"  Generated : {generated}")
    print(f"  Skipped   : {skipped}")
    print(f"  Errors    : {errors}")
    print(f"  Time      : {elapsed:.1f}s ({elapsed/max(generated,1):.1f}s per file)")
    print()

    if errors == 0 and generated > 0:
        print(f"  ✓ Success! Audio files ready in audio/ directory.")
        print(f"  ✓ Open brahma-vihara-meditation-app.html in a browser to listen.")
    elif errors > 0:
        print(f"  ⚠ {errors} file(s) failed. Check ffmpeg and Chatterbox installation.")

if __name__ == "__main__":
    main()
