"""
Audio capture from local microphone.

Records audio to WAV files in 01-witnesses/audio/.
Provides terminal-based level meter feedback.
"""

import sys
import time
import threading
import numpy as np
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent
AUDIO_DIR = VAULT_ROOT / "01-witnesses" / "audio"

# Defaults — overridden by config/voice.yaml if present
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1
DEFAULT_SILENCE_THRESHOLD = 0.01
DEFAULT_SILENCE_DURATION = 3.0


def ensure_dirs():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def generate_filename() -> str:
    """Generate timestamped filename: voice_YYYYMMDD_HHmm.wav"""
    now = datetime.now()
    return now.strftime("voice_%Y%m%d_%H%M.wav")


def level_meter(rms: float, width: int = 40) -> str:
    """Render a terminal-based level meter from RMS amplitude."""
    level = min(int(rms * width * 10), width)  # scale for visibility
    bar = "\u2588" * level + "\u2591" * (width - level)
    return f"\r  [{bar}] {rms:.4f}"


def record(
    output_path: Path = None,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    channels: int = DEFAULT_CHANNELS,
    silence_threshold: float = DEFAULT_SILENCE_THRESHOLD,
    silence_duration: float = DEFAULT_SILENCE_DURATION,
    max_duration: float = 300.0,
) -> Path:
    """
    Record audio from the default microphone.

    Press Enter to stop recording. Auto-stops after silence_duration
    seconds of silence below silence_threshold, or after max_duration.

    Returns the path to the saved WAV file.
    """
    try:
        import sounddevice as sd
        import soundfile as sf
    except ImportError:
        print("Missing dependencies. Install with:")
        print("  pip install sounddevice soundfile")
        sys.exit(1)

    ensure_dirs()

    if output_path is None:
        output_path = AUDIO_DIR / generate_filename()

    frames = []
    silence_start = None
    is_recording = True
    stop_event = threading.Event()

    def on_enter():
        """Wait for Enter key in a separate thread."""
        input()
        stop_event.set()

    enter_thread = threading.Thread(target=on_enter, daemon=True)

    print(f"  Recording to: {output_path.name}")
    print(f"  Sample rate:  {sample_rate} Hz")
    print(f"  Press Enter to stop (auto-stops after {silence_duration}s silence)")
    print()

    enter_thread.start()

    try:
        with sd.InputStream(
            samplerate=sample_rate,
            channels=channels,
            dtype="float32",
            blocksize=int(sample_rate * 0.1),  # 100ms blocks
        ) as stream:
            start_time = time.time()

            while not stop_event.is_set():
                data, overflowed = stream.read(int(sample_rate * 0.1))
                frames.append(data.copy())

                # Level meter
                rms = float(np.sqrt(np.mean(data**2)))
                sys.stdout.write(level_meter(rms))
                sys.stdout.flush()

                # Silence detection
                if rms < silence_threshold:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > silence_duration:
                        print("\n  Auto-stopped: silence detected")
                        break
                else:
                    silence_start = None

                # Max duration
                elapsed = time.time() - start_time
                if elapsed >= max_duration:
                    print(f"\n  Auto-stopped: max duration ({max_duration}s)")
                    break

    except KeyboardInterrupt:
        print("\n  Recording stopped.")

    if not frames:
        print("  No audio captured.")
        return None

    # Concatenate and save
    audio = np.concatenate(frames, axis=0)
    sf.write(str(output_path), audio, sample_rate)

    duration = len(audio) / sample_rate
    print(f"\n  Saved: {output_path}")
    print(f"  Duration: {duration:.1f}s")

    return output_path


def list_devices():
    """List available audio input devices."""
    try:
        import sounddevice as sd
    except ImportError:
        print("Missing dependency: pip install sounddevice")
        sys.exit(1)

    print("  Available audio input devices:")
    print()
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            default = " (default)" if i == sd.default.device[0] else ""
            print(f"  [{i}] {dev['name']}{default}")
            print(f"      Channels: {dev['max_input_channels']}, "
                  f"Sample Rate: {int(dev['default_samplerate'])} Hz")
