# Architecture Overview

The Explainer Video Factory is a multi-modal rendering pipeline designed to convert complex topics into educational videos automatically.

## Core Design Philosophy

1. **Multi-Agent Orchestration**: Specialized agents handle distinct modalities (Avatar for audio/narration, Visuals for imagery, Synthesis for combination).
2. **Deterministic State Machine**: LangGraph ensures the pipeline executes reliably, managing dependencies between audio timing and visual assembly.
3. **Hardware Independence**: CPU-bound tools (Pillow for images, edge-tts for audio, MoviePy for video) ensure the project runs anywhere without requiring complex GPU configurations.
4. **Offline First**: Template-based script generation allows demo generation without relying on external LLM APIs by default.

## Pipeline Components

1. **Script Generator**: Produces segmented educational scripts.
2. **Scene Planner**: Breaks scripts into a timeline of discrete visual scenes.
3. **TTS Renderer**: Generates high-quality speech with word-level timing metadata.
4. **Visual Renderer**: Produces stylized 1080p PNG images for each scene.
5. **Video Composer**: Aligns audio and visual clips temporally and encodes the final MP4.
6. **Subtitle Renderer**: Generates synchronized SRT subtitle files.

## Data Flow

`Topic -> Script -> Planned Scenes -> [Audio Assets | Visual Assets] -> Timeline Assembly -> Final MP4`
