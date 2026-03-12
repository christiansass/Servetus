"""
Local transcription using faster-whisper.

Runs entirely offline after initial model download.
Returns segments with word-level timestamps.
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Word:
    text: str
    start: float
    end: float
    probability: float


@dataclass
class Segment:
    id: int
    text: str
    start: float
    end: float
    confidence: float
    words: list = field(default_factory=list)


@dataclass
class TranscriptionResult:
    segments: list
    language: str
    language_probability: float
    duration: float
    model: str
    text: str = ""

    def __post_init__(self):
        if not self.text:
            self.text = " ".join(seg.text.strip() for seg in self.segments)


def transcribe(
    audio_path: Path,
    model_size: str = "base",
    language: str = None,
    device: str = "auto",
) -> TranscriptionResult:
    """
    Transcribe an audio file using faster-whisper.

    Args:
        audio_path: Path to WAV/FLAC audio file
        model_size: Whisper model — tiny, base, small, medium, large-v3
        language: Language hint (None for auto-detect)
        device: Compute device — auto, cpu, cuda

    Returns:
        TranscriptionResult with segments, words, and timestamps
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("Missing dependency. Install with:")
        print("  pip install faster-whisper")
        sys.exit(1)

    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Resolve compute device
    if device == "auto":
        compute_type = "int8"
        device = "cpu"
        try:
            import torch
            if torch.cuda.is_available():
                device = "cuda"
                compute_type = "float16"
        except ImportError:
            pass

    print(f"  Loading model: {model_size} (device: {device})")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    print(f"  Transcribing: {audio_path.name}")
    segments_raw, info = model.transcribe(
        str(audio_path),
        language=language,
        word_timestamps=True,
        vad_filter=True,
    )

    segments = []
    for i, seg in enumerate(segments_raw):
        words = []
        if seg.words:
            for w in seg.words:
                words.append(Word(
                    text=w.word,
                    start=w.start,
                    end=w.end,
                    probability=w.probability,
                ))

        segments.append(Segment(
            id=i + 1,
            text=seg.text.strip(),
            start=seg.start,
            end=seg.end,
            confidence=seg.avg_logprob,
            words=words,
        ))

    result = TranscriptionResult(
        segments=segments,
        language=info.language,
        language_probability=info.language_probability,
        duration=info.duration,
        model=model_size,
    )

    print(f"  Language: {result.language} ({result.language_probability:.0%})")
    print(f"  Segments: {len(result.segments)}")
    print(f"  Duration: {result.duration:.1f}s")

    return result
