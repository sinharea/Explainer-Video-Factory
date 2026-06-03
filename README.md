# Explainer Video Factory 🏭🎥

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A multi-modal synchronous rendering pipeline that automatically transforms educational topics into polished, synchronized explainer videos. 

Built with **LangGraph**, **edge-tts**, **Pillow**, and **MoviePy**, this tool uses a specialized multi-agent architecture to orchestrate script generation, dynamic visual rendering, and audio narration into a unified timeline.

---

## 🌟 Features

* **Multi-Agent Orchestration**: Uses LangGraph to manage dedicated Avatar, Visuals, and Synthesis agents.
* **Synchronized Timeline**: Automatically aligns audio narration length with visual scene display time.
* **CPU-Bound Rendering**: Generates beautiful 1080p visuals using Pillow and Cairo — no GPU required!
* **High-Quality TTS**: Uses Microsoft Edge TTS for natural, expressive narration.
* **Template & LLM Scripting**: Includes offline educational templates with fallback to LLM (OpenAI/Anthropic) integration.
* **FastAPI Server**: Includes an async API for triggering and monitoring background rendering jobs.

## 🏗️ Architecture

The factory pipeline operates in several distinct stages, orchestrated by LangGraph:

1. **Script Generation (Avatar Agent)**: Expands a given topic into an educational script broken down into logical segments.
2. **Scene Planning (Visuals Agent)**: Parses the script segments and assigns visual templates (Title, Diagram, Analogy, etc.).
3. **Parallel Rendering**:
   - *Avatar Agent* generates TTS audio and extracts word-level timing.
   - *Visuals Agent* draws 1080p PNG images based on the assigned theme and scene type.
4. **Synthesis (Synthesis Agent)**: Assembles the generated audio and images using MoviePy, applies transitions, generates SRT subtitles, and encodes the final MP4.

*For more details, see [Architecture](docs/architecture.md) and [Agent Workflow](docs/agent_workflow.md).*

## 🚀 Quickstart

### Prerequisites

- Python 3.10 or higher
- System `ffmpeg` is **not** required! (Provided via `imageio-ffmpeg`)

### Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/sinharea/Explainer-Video-Factory.git
cd Explainer-Video-Factory

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package and dependencies
make install
```

### Running the CLI Demo

Generate a complete video about "Quantum Entanglement" directly from the command line:

```bash
make run-demo
```
*Outputs will be saved in `examples/outputs/`.*

### Starting the API Server

Launch the FastAPI background worker server:

```bash
make run-api
```
*API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).*

## 📁 Project Structure

```
Explainer-Video-Factory/
├── src/explainer_factory/
│   ├── agents/         # LangChain/LangGraph Agents (Avatar, Visuals, Synthesis)
│   ├── api/            # FastAPI application and routes
│   ├── models/         # Pydantic data models for state management
│   ├── orchestrator/   # LangGraph state machine definition
│   ├── pipeline/       # Script, Scene, and Timeline logic
│   ├── renderers/      # TTS, Visual, and Video rendering engines
│   └── utils/          # File and media helpers
├── tests/              # Pytest test suite
├── scripts/            # CLI runners and demo scripts
├── docs/               # Architecture and workflow documentation
└── assets/             # Fonts, templates, and themes
```

## 🛠️ Configuration

Configuration is managed via `pydantic-settings`. Create a `.env` file from the example:

```bash
cp .env.example .env
```

Key settings include:
- `VIDEO_WIDTH` / `VIDEO_HEIGHT`: Output resolution (Default: 1920x1080)
- `TTS_VOICE`: edge-tts voice model (Default: `en-US-AriaNeural`)
- `LLM_PROVIDER`: Set to `openai` or `anthropic` to enable dynamic script generation.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
