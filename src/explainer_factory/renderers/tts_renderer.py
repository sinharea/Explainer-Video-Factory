"""Text-to-Speech rendering engine using edge-tts.

Generates high-quality speech audio from text segments with
timing metadata for synchronization.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import edge_tts

from explainer_factory.config import TTSSettings
from explainer_factory.exceptions import TTSRenderError
from explainer_factory.logging import get_logger

logger = get_logger(__name__)


def _probe_audio_duration(file_path: Path) -> float:
    """Get the true duration of an audio file by decoding it.

    Uses moviepy's AudioFileClip which reads the actual audio stream,
    giving us the ground-truth playback duration in seconds.

    Args:
        file_path: Path to the audio file.

    Returns:
        Duration in seconds.
    """
    try:
        from moviepy import AudioFileClip
        clip = AudioFileClip(str(file_path))
        duration = clip.duration
        clip.close()
        return duration
    except Exception:
        # Fallback: rough estimate from file size (~16 kBps for MP3)
        if file_path.exists():
            return file_path.stat().st_size / 16000.0
        return 0.0


class TTSRenderer:
    """Renders text to speech audio using Microsoft Edge TTS.

    Produces MP3 audio files with word-level timing metadata
    for accurate lip-sync and subtitle generation.
    """

    def __init__(self, settings: TTSSettings | None = None):
        """Initialize TTS renderer.

        Args:
            settings: TTS configuration. Uses defaults if not provided.
        """
        self.settings = settings or TTSSettings()
        logger.info(
            "tts_renderer.init",
            voice=self.settings.voice,
            rate=self.settings.rate,
        )

    async def render_segment_async(
        self,
        text: str,
        output_path: Path,
    ) -> dict:
        """Render a single text segment to audio asynchronously.

        Args:
            text: Text to synthesize.
            output_path: Path to write the audio file.

        Returns:
            Dict with 'path', 'duration', and 'word_timings'.

        Raises:
            TTSRenderError: If synthesis fails.
        """
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.settings.voice,
                rate=self.settings.rate,
                volume=self.settings.volume,
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            word_timings = []

            # Stream audio to file and collect timing metadata
            with open(output_path, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        word_timings.append({
                            "word": chunk["text"],
                            "offset": chunk["offset"] / 10_000_000,  # ticks to seconds
                            "duration": chunk["duration"] / 10_000_000,
                        })

            # Always probe the actual file for ground-truth duration.
            # Word-boundary timing from edge-tts is unreliable and often
            # returns 0 words, causing massive drift between estimated
            # and real audio length.
            duration = _probe_audio_duration(output_path)

            logger.info(
                "tts_renderer.segment_done",
                output=str(output_path),
                duration=f"{duration:.2f}s",
                words=len(word_timings),
            )

            return {
                "path": output_path,
                "duration": duration,
                "word_timings": word_timings,
            }

        except Exception as e:
            raise TTSRenderError(
                f"TTS rendering failed for segment",
                details={"text_preview": text[:80], "error": str(e)},
            ) from e

    def render_segment(self, text: str, output_path: Path) -> dict:
        """Synchronous wrapper for render_segment_async.

        Args:
            text: Text to synthesize.
            output_path: Path to write the audio file.

        Returns:
            Dict with 'path', 'duration', and 'word_timings'.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in an async context, create a new loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.render_segment_async(text, output_path),
                    )
                    return future.result()
        except RuntimeError:
            pass

        return asyncio.run(self.render_segment_async(text, output_path))

    async def render_all_scenes_async(
        self,
        scenes: list,
        output_dir: Path,
    ) -> dict[str, dict]:
        """Render audio for all scenes.

        Args:
            scenes: List of Scene objects with narration text.
            output_dir: Directory to write audio files.

        Returns:
            Mapping of scene_id -> render result dict.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        results: dict[str, dict] = {}

        logger.info("tts_renderer.batch_start", num_scenes=len(scenes))

        for scene in scenes:
            audio_path = output_dir / f"{scene.scene_id}.mp3"
            result = await self.render_segment_async(
                text=scene.narration,
                output_path=audio_path,
            )
            results[scene.scene_id] = result
            scene.audio_path = audio_path

        logger.info(
            "tts_renderer.batch_complete",
            num_rendered=len(results),
            total_duration=f"{sum(r['duration'] for r in results.values()):.1f}s",
        )
        return results

    def render_all_scenes(self, scenes: list, output_dir: Path) -> dict[str, dict]:
        """Synchronous wrapper for render_all_scenes_async."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.render_all_scenes_async(scenes, output_dir),
                    )
                    return future.result()
        except RuntimeError:
            pass

        return asyncio.run(self.render_all_scenes_async(scenes, output_dir))
