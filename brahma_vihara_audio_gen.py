#!/usr/bin/env python3
"""
Brahma Vihara Audio Generator
==============================
Generates all 169 guided meditation MP3s using ElevenLabs API.
One sentence per file, named by phase and index.

Usage:
    python brahma_vihara_audio_gen.py                     # generate all missing
    python brahma_vihara_audio_gen.py --phase metta       # one phase only
    python brahma_vihara_audio_gen.py --dry-run           # preview, no API calls
    python brahma_vihara_audio_gen.py --force             # regenerate even if exists
    python brahma_vihara_audio_gen.py --list-voices       # show available voices
    python brahma_vihara_audio_gen.py --estimate          # show cost estimate only

Setup:
    1. pip install elevenlabs
    2. export ELEVENLABS_API_KEY=your_key_here
       (or paste your key into API_KEY below)
    3. python brahma_vihara_audio_gen.py --list-voices
       (pick the voice you want, paste its ID into VOICE_ID below)
    4. python brahma_vihara_audio_gen.py --dry-run --phase settle
    5. python brahma_vihara_audio_gen.py

Output:
    audio/settle_01.mp3  through  audio/close_15.mp3
    (169 files total, ~45–80KB each, ~12MB total)
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# CONFIGURATION — edit these
# ─────────────────────────────────────────────────────────────

API_KEY = os.environ.get("ELEVENLABS_API_KEY", "YOUR_KEY_HERE")

# Voice settings — run --list-voices to find the right ID
# Recommended voices for meditative guidance:
#   Rachel    (warm, gentle female)  : 21m00Tcm4TlvDq8ikWAM
#   Adam      (calm male)            : pNInz6obpgDQGcFmaJgB  
#   Serene    (soft female)          : stAqIqVMhHinrKQi3XNV  — ideal for meditation
#   Bella     (warm female)          : EXAVITQu4vr4xnSDxMaL
#   Clyde     (warm male)            : 2EiwWnXFnvU5JabPnv8n
VOICE_ID   = "stAqIqVMhHinrKQi3XNV"   # ← change this to your preferred voice

# Voice settings — tune these for meditative quality
VOICE_SETTINGS = {
    "stability":        0.85,   # 0–1. Higher = more consistent, less variation
    "similarity_boost": 0.75,   # 0–1. How closely it matches the original voice
    "style":            0.20,   # 0–1. 0 = neutral, 1 = very expressive
    "use_speaker_boost": True,  # Enhances clarity — recommended
    "speed":            0.82,   # 0.5–2.0. 0.82 = slow meditative pace
}

MODEL_ID   = "eleven_turbo_v2_5"  # Fastest + cheapest. Use "eleven_multilingual_v2" for richer quality
OUTPUT_DIR = Path("audio")
MANIFEST   = Path("audio_manifest.json")

# ─────────────────────────────────────────────────────────────
# MANIFEST (all 169 segments — generated from the app)
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
# VOICES RECOMMENDED FOR MEDITATION
# ─────────────────────────────────────────────────────────────
RECOMMENDED_VOICES = {
    "Serene":  {"id": "stAqIqVMhHinrKQi3XNV", "note": "Soft, warm female — best for meditation"},
    "Rachel":  {"id": "21m00Tcm4TlvDq8ikWAM", "note": "Warm, gentle female — very natural"},
    "Bella":   {"id": "EXAVITQu4vr4xnSDxMaL", "note": "Soft female — calm and clear"},
    "Adam":    {"id": "pNInz6obpgDQGcFmaJgB", "note": "Neutral male — calm and steady"},
    "Clyde":   {"id": "2EiwWnXFnvU5JabPnv8n", "note": "Warm male — grounded presence"},
    "Dorothy": {"id": "ThT5KcBeYPX3keUQqHPh", "note": "Warm British female — gentle authority"},
}

# ─────────────────────────────────────────────────────────────
# GENERATOR
# ─────────────────────────────────────────────────────────────

def estimate_cost(segments):
    """ElevenLabs charges per character. Turbo v2.5 = $0.0003/1k chars."""
    total_chars = sum(len(s["text"]) for s in segments)
    cost = (total_chars / 1000) * 0.30   # $0.30 per 1k chars (turbo_v2.5)
    return total_chars, cost

def list_voices(client):
    print("\nAvailable voices on your account:\n")
    voices = client.voices.get_all()
    for v in voices.voices:
        print(f"  {v.name:<20} {v.voice_id}  — {v.labels}")
    print("\nRecommended for meditation:")
    for name, info in RECOMMENDED_VOICES.items():
        print(f"  {name:<12} {info['id']}  — {info['note']}")

def generate_audio(client, segment, output_path, dry_run=False):
    """Generate one MP3 for a single text segment."""
    if dry_run:
        print(f"  [DRY RUN] Would generate: {output_path.name}  \"{segment['text'][:55]}\"")
        return True

    try:
        audio = client.text_to_speech.convert(
            voice_id=VOICE_ID,
            text=segment["text"],
            model_id=MODEL_ID,
            voice_settings={
                "stability":         VOICE_SETTINGS["stability"],
                "similarity_boost":  VOICE_SETTINGS["similarity_boost"],
                "style":             VOICE_SETTINGS["style"],
                "use_speaker_boost": VOICE_SETTINGS["use_speaker_boost"],
            },
            # Speed via SSML-style tag — only works on v2 models
            # For turbo: use output_format and rely on voice_settings
        )
        # Write bytes to file
        output_path.write_bytes(b"".join(audio))
        return True
    except Exception as e:
        print(f"  ✗ ERROR {output_path.name}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate Brahma Vihara guided meditation audio")
    parser.add_argument("--phase",       help="Only generate one phase: settle|metta|karuna|mudita|upekkha|close")
    parser.add_argument("--dry-run",     action="store_true", help="Preview without making API calls")
    parser.add_argument("--force",       action="store_true", help="Regenerate even if file already exists")
    parser.add_argument("--list-voices", action="store_true", help="List available ElevenLabs voices")
    parser.add_argument("--estimate",    action="store_true", help="Show cost estimate only")
    args = parser.parse_args()

    # Validate API key
    if API_KEY == "YOUR_KEY_HERE" and not args.dry_run:
        print("✗  Set your ElevenLabs API key:")
        print("   export ELEVENLABS_API_KEY=your_key_here")
        print("   or edit API_KEY in this script")
        sys.exit(1)

    # Import ElevenLabs
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import VoiceSettings
    except ImportError:
        print("✗  elevenlabs not installed. Run: pip install elevenlabs")
        sys.exit(1)

    client = ElevenLabs(api_key=API_KEY)

    if args.list_voices:
        list_voices(client)
        return

    # Filter segments
    segments = SEGMENTS
    if args.phase:
        segments = [s for s in segments if s["phase"] == args.phase]
        if not segments:
            print(f"✗  Phase '{args.phase}' not found. Valid: settle metta karuna mudita upekkha close")
            sys.exit(1)

    # Cost estimate
    total_chars, cost = estimate_cost(segments)
    print(f"\nBrahma Vihara Audio Generator")
    print(f"{'─'*50}")
    print(f"  Segments to generate : {len(segments)}")
    print(f"  Total characters     : {total_chars:,}")
    print(f"  Estimated cost       : ${cost:.4f}  (ElevenLabs turbo_v2.5)")
    print(f"  Voice ID             : {VOICE_ID}")
    print(f"  Output directory     : {OUTPUT_DIR}/")
    print(f"  Model                : {MODEL_ID}")
    if args.dry_run:   print(f"  Mode                 : DRY RUN — no API calls")
    if args.force:     print(f"  Mode                 : FORCE — regenerating all")
    print()

    if args.estimate:
        return

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Generate
    generated = 0
    skipped   = 0
    errors    = 0

    for i, seg in enumerate(segments, 1):
        out_path = OUTPUT_DIR / seg["filename"]

        if out_path.exists() and not args.force and not args.dry_run:
            print(f"  [{i:03d}/{len(segments)}] ⟳ skip  {seg['filename']}")
            skipped += 1
            continue

        print(f"  [{i:03d}/{len(segments)}] ▶ gen   {seg['filename']}  \"{seg['text'][:50]}\"")
        ok = generate_audio(client, seg, out_path, dry_run=args.dry_run)
        if ok:
            generated += 1
        else:
            errors += 1

        # Rate limit: ElevenLabs free tier = 2 req/sec; paid = higher
        # Small delay to be safe
        if not args.dry_run:
            time.sleep(0.35)

    # Summary
    print(f"\n{'─'*50}")
    print(f"  Generated : {generated}")
    print(f"  Skipped   : {skipped}  (already exist)")
    print(f"  Errors    : {errors}")
    if generated > 0 and not args.dry_run:
        actual_cost = sum(len(s["text"]) for s in segments[:generated]) / 1000 * 0.30
        print(f"  Est. cost : ${actual_cost:.4f}")
    print()
    if errors == 0 and not args.dry_run and not args.dry_run:
        print("  ✓ All done. Copy the 'audio/' folder next to your HTML file.")
        print("  ✓ Then open brahma-vihara-meditation-app.html in a browser.")

if __name__ == "__main__":
    main()
