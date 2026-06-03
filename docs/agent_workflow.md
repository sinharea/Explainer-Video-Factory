# Agent Workflow

The system utilizes LangGraph to orchestrate three specialized agents.

## 1. Avatar Agent
- **Responsibilities**: Narration generation, audio rendering, and speech timing.
- **Tools**: LangChain (optional LLM), edge-tts (Text-to-Speech).
- **Output**: Populated `audio_path` and exact `duration` for each scene.

## 2. Visuals Agent
- **Responsibilities**: Scene planning, layout generation, image rendering.
- **Tools**: Pillow (Python Imaging Library).
- **Output**: Populated `visual_path` for each scene.

## 3. Synthesis Agent
- **Responsibilities**: Timeline alignment, subtitle generation, and video encoding.
- **Tools**: MoviePy, Timeline Manager.
- **Output**: Final `output_video` and `output_subtitle` paths.

## LangGraph State Machine
The orchestrator maintains a `PipelineState` dict tracking the `RenderJob`. 
It routes the job sequentially through Script Generation and Scene Planning, then branches parallelly to Audio and Visual Rendering, finally joining at Synthesis.
