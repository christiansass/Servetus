"""
Prosodic analysis — extract how words were spoken, not just what was said.

Uses parselmouth (Praat) for pitch and librosa/numpy for energy analysis.
Generates SVP (Servetus Voice Performance) files.
"""

import numpy as np
from pathlib import Path
from datetime import datetime


def _format_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def _classify_volume(rms: float) -> str:
    """Classify RMS energy into volume labels."""
    if rms < 0.005:
        return "whisper"
    elif rms < 0.015:
        return "quiet"
    elif rms < 0.05:
        return "moderate"
    elif rms < 0.15:
        return "loud"
    else:
        return "shouting"


def _classify_pitch(mean_pitch: float, pitch_slope: float) -> str:
    """Classify pitch into contour labels based on mean and slope."""
    # Determine level
    if mean_pitch < 120:
        level = "low"
    elif mean_pitch < 200:
        level = "mid"
    else:
        level = "high"

    # Determine direction
    if abs(pitch_slope) < 5:
        direction = "flat"
    elif pitch_slope > 0:
        direction = "rising"
    else:
        direction = "falling"

    return f"{level}-{direction}"


def _classify_emotion(
    pace: float, volume: str, pitch_contour: str, pitch_variability: float
) -> str:
    """
    Estimate emotional register from prosodic features.

    This is a rough heuristic, not sentiment analysis. It encodes
    observable vocal characteristics, not inner states.
    """
    if volume == "whisper" and "low" in pitch_contour:
        return "contemplative"
    if volume in ("loud", "shouting") and pace > 160:
        return "excited"
    if "rising" in pitch_contour and pace > 140:
        return "uncertain"
    if volume in ("loud", "shouting") and "flat" in pitch_contour:
        return "emphatic"
    if "falling" in pitch_contour and pace < 110:
        return "resigned"
    if pitch_variability > 40 and pace > 130:
        return "passionate"
    if pitch_variability > 30:
        return "amused"
    return "neutral"


def _classify_pause(duration_ms: float, prev_text: str = "") -> str:
    """Classify a pause by its duration and context."""
    if duration_ms < 300:
        return "breath"
    elif duration_ms < 1500:
        if prev_text and prev_text.rstrip().endswith(("um", "uh", "er", "ah")):
            return "hesitation"
        return "deliberate"
    else:
        return "long"


def analyze(audio_path: Path, transcription_result) -> dict:
    """
    Analyze prosodic features of an audio file against its transcription.

    Args:
        audio_path: Path to the WAV file
        transcription_result: TranscriptionResult from transcribe.py

    Returns:
        dict with 'segments' (annotated) and 'pauses' lists
    """
    try:
        import soundfile as sf
    except ImportError:
        raise ImportError("pip install soundfile")

    audio, sample_rate = sf.read(str(audio_path))
    if len(audio.shape) > 1:
        audio = audio[:, 0]  # mono

    # Try parselmouth for pitch, fall back to basic analysis
    has_praat = False
    try:
        import parselmouth
        sound = parselmouth.Sound(audio, sampling_frequency=sample_rate)
        pitch_obj = sound.to_pitch()
        has_praat = True
    except ImportError:
        pass

    annotated_segments = []
    pauses = []
    prev_end = 0.0

    for seg in transcription_result.segments:
        # Detect pause before this segment
        gap = seg.start - prev_end
        if gap > 0.15:  # ignore gaps < 150ms
            pause_type = _classify_pause(
                gap * 1000,
                annotated_segments[-1]["text"] if annotated_segments else "",
            )
            pauses.append({
                "start": prev_end,
                "end": seg.start,
                "duration_ms": int(gap * 1000),
                "type": pause_type,
            })

        # Extract audio slice for this segment
        start_sample = int(seg.start * sample_rate)
        end_sample = int(seg.end * sample_rate)
        segment_audio = audio[start_sample:end_sample]

        # RMS energy
        rms = float(np.sqrt(np.mean(segment_audio**2))) if len(segment_audio) > 0 else 0

        # Speaking pace (words per minute)
        word_count = len(seg.text.split())
        duration = seg.end - seg.start
        pace = int(word_count / duration * 60) if duration > 0 else 0

        # Pitch analysis
        mean_pitch = 0.0
        pitch_slope = 0.0
        pitch_variability = 0.0

        if has_praat and duration > 0:
            pitch_values = []
            for t in np.linspace(seg.start, seg.end, num=20):
                p = pitch_obj.get_value_at_time(t)
                if p and not np.isnan(p):
                    pitch_values.append(p)

            if pitch_values:
                mean_pitch = np.mean(pitch_values)
                pitch_variability = np.std(pitch_values)
                if len(pitch_values) > 1:
                    # Simple linear slope
                    x = np.arange(len(pitch_values))
                    pitch_slope = float(np.polyfit(x, pitch_values, 1)[0])

        volume = _classify_volume(rms)
        pitch_contour = _classify_pitch(mean_pitch, pitch_slope)
        emotion = _classify_emotion(pace, volume, pitch_contour, pitch_variability)

        # Find emphasized words (energy spikes relative to segment average)
        emphasis_words = set()
        if seg.words and len(segment_audio) > 0:
            seg_rms = rms
            for word in seg.words:
                ws = int(word.start * sample_rate)
                we = int(word.end * sample_rate)
                word_audio = audio[ws:we]
                if len(word_audio) > 0:
                    word_rms = float(np.sqrt(np.mean(word_audio**2)))
                    if word_rms > seg_rms * 1.5:
                        emphasis_words.add(word.text.strip())

        annotated_segments.append({
            "id": seg.id,
            "start": seg.start,
            "end": seg.end,
            "text": seg.text,
            "pace": pace,
            "volume": volume,
            "pitch": pitch_contour,
            "emotion": emotion,
            "confidence": seg.confidence,
            "emphasis_words": emphasis_words,
            "words": seg.words,
        })

        prev_end = seg.end

    return {
        "segments": annotated_segments,
        "pauses": pauses,
    }


def generate_svp(
    audio_path: Path,
    transcription_result,
    prosody_result: dict,
    speaker: str = "",
) -> str:
    """
    Generate an SVP (Servetus Voice Performance) file content.

    Returns the SVP content as a string.
    """
    lines = []

    # Header
    lines.append("#SVP v1")
    lines.append(f"#source: {audio_path.name}")
    lines.append(f"#model: whisper-{transcription_result.model}")
    lines.append(f"#prosody_engine: servetus-voice/0.1.0")
    lines.append(f"#analyzed: {datetime.now().astimezone().isoformat()}")
    lines.append(f"#duration: {transcription_result.duration:.1f}s")
    if speaker:
        lines.append(f"#speaker: {speaker}")
    lines.append("")

    # Interleave segments and pauses
    pause_idx = 0
    pauses = prosody_result["pauses"]

    for seg in prosody_result["segments"]:
        # Insert any pauses before this segment
        while pause_idx < len(pauses) and pauses[pause_idx]["end"] <= seg["start"] + 0.01:
            p = pauses[pause_idx]
            lines.append(
                f"@pause [{_format_time(p['start'])} \u2192 {_format_time(p['end'])}] "
                f"{p['duration_ms']}ms {p['type']}"
            )
            lines.append("")
            pause_idx += 1

        # Segment
        lines.append(
            f"@segment {seg['id']} "
            f"[{_format_time(seg['start'])} \u2192 {_format_time(seg['end'])}]"
        )
        lines.append(
            f"| pace: {seg['pace']} | volume: {seg['volume']} | pitch: {seg['pitch']} |"
        )

        # Normalize confidence to 0-1 range (whisper logprobs are negative)
        conf = min(1.0, max(0.0, 1.0 + seg["confidence"]))  # logprob → approx probability
        lines.append(
            f"| emotion: {seg['emotion']} | confidence: {conf:.2f} |"
        )

        # Text with emphasis markers
        text = seg["text"]
        for word in seg.get("emphasis_words", set()):
            text = text.replace(word, f"*{word}*")
        lines.append(f'"{text}"')
        lines.append("")

    return "\n".join(lines)


def write_svp(svp_content: str, audio_path: Path) -> Path:
    """Write SVP content to a file alongside the audio."""
    svp_dir = audio_path.parent.parent / "svp"
    svp_dir.mkdir(parents=True, exist_ok=True)

    svp_path = svp_dir / (audio_path.stem + ".svp")
    svp_path.write_text(svp_content, encoding="utf-8")

    print(f"  SVP written: {svp_path}")
    return svp_path
