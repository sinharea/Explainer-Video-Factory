"""Audio processing utilities."""

from pathlib import Path


def get_audio_duration(file_path: Path) -> float:
    """Get the duration of an audio file in seconds.
    
    Fallback utility if metadata timing fails. Requires pydub.
    """
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(str(file_path))
        return len(audio) / 1000.0
    except ImportError:
        # Fallback to estimation based on file size if pydub is missing
        if file_path.exists():
            return file_path.stat().st_size / 16000.0
        return 0.0
