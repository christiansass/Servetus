"""
Voice pipeline — the main orchestrator.

Ties together capture → transcribe → analyze → witness
in a single flow.
"""

import sys
from pathlib import Path

from . import __version__
from .capture import record, list_devices, AUDIO_DIR
from .transcribe import transcribe
from .prosody import analyze, generate_svp, write_svp
from .witness import create_witness


def run(
    audio_file: str = None,
    model: str = "base",
    language: str = None,
    speaker: str = "",
    skip_prosody: bool = False,
    show_devices: bool = False,
):
    """
    Run the full voice pipeline.

    If audio_file is provided, process it. Otherwise, record from mic.
    """
    if show_devices:
        list_devices()
        return

    print(f"\n  Servetus Voice Pipeline v{__version__}")
    print(f"  {'=' * 40}\n")

    # Step 1: Capture (or use existing file)
    if audio_file:
        audio_path = Path(audio_file)
        if not audio_path.exists():
            print(f"  Error: File not found: {audio_file}")
            sys.exit(1)
        print(f"  Using existing audio: {audio_path}")
    else:
        print("  STEP 1: Audio Capture")
        print(f"  {'-' * 30}")
        audio_path = record()
        if audio_path is None:
            print("  No audio recorded. Exiting.")
            return
        print()

    # Step 2: Transcribe
    print("  STEP 2: Transcription (local)")
    print(f"  {'-' * 30}")
    result = transcribe(audio_path, model_size=model, language=language)
    print()

    if not result.segments:
        print("  No speech detected in audio.")
        return

    # Step 3: Prosodic analysis
    svp_path = None
    if not skip_prosody:
        print("  STEP 3: Prosodic Analysis")
        print(f"  {'-' * 30}")
        prosody = analyze(audio_path, result)
        svp_content = generate_svp(audio_path, result, prosody, speaker=speaker)
        svp_path = write_svp(svp_content, audio_path)
        print(f"  Segments analyzed: {len(prosody['segments'])}")
        print(f"  Pauses detected:  {len(prosody['pauses'])}")
        print()
    else:
        print("  STEP 3: Prosodic Analysis (skipped)")
        print()

    # Step 4: Create witness
    print("  STEP 4: Witness Creation")
    print(f"  {'-' * 30}")
    if svp_path is None:
        # Create a minimal SVP placeholder path for the witness
        from .prosody import write_svp as _ws
        svp_dir = audio_path.parent.parent / "svp"
        svp_dir.mkdir(parents=True, exist_ok=True)
        svp_path = svp_dir / (audio_path.stem + ".svp")
        svp_path.write_text(f"#SVP v1\n#source: {audio_path.name}\n#note: prosody skipped\n")

    witness_path = create_witness(audio_path, svp_path, result, speaker=speaker)
    print()

    # Summary
    print(f"  {'=' * 40}")
    print(f"  DONE")
    print(f"  Audio:   {audio_path}")
    print(f"  SVP:     {svp_path}")
    print(f"  Witness: {witness_path}")
    print(f"  Text:    {result.text[:80]}{'...' if len(result.text) > 80 else ''}")
    print()

    return {
        "audio_path": audio_path,
        "svp_path": svp_path,
        "witness_path": witness_path,
        "transcription": result,
    }
