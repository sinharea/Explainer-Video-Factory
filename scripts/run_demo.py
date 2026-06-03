"""Command-line interface for the Explainer Video Factory."""

import argparse
import sys
from pathlib import Path

from explainer_factory import __version__
from explainer_factory.config import get_settings
from explainer_factory.logging import get_logger, setup_logging
from explainer_factory.models.render_job import RenderJob
from explainer_factory.orchestrator.graph import PipelineOrchestrator

logger = get_logger(__name__)


def main() -> int:
    """Run the CLI application."""
    parser = argparse.ArgumentParser(
        description="Explainer Video Factory - CLI Demo Runner"
    )
    parser.add_argument(
        "--topic", 
        type=str, 
        required=True,
        help="The educational topic to explain (e.g., 'Quantum Entanglement')"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./examples/outputs",
        help="Directory to save the generated outputs"
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use LLM for script generation (requires API keys)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Setup environment
    settings = get_settings()
    log_level = "DEBUG" if args.verbose else settings.log_level
    setup_logging(level=log_level, log_format=settings.log_format)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("cli.start", version=__version__, topic=args.topic)
    
    try:
        # Initialize job
        job = RenderJob(topic=args.topic)
        job_dir = output_dir / job.job_id
        job_dir.mkdir(exist_ok=True)
        job.output_dir = job_dir
        
        # We pass use_llm via settings or env in a real app, 
        # but for this demo the script generator uses it directly if instantiated.
        # Our orchestrator initializes agents with defaults, so it will use templates.
        
        # Run orchestrator
        orchestrator = PipelineOrchestrator()
        logger.info(f"Starting render pipeline for topic: '{args.topic}'")
        
        job = orchestrator.run(job)
        
        if job.output_video and job.output_video.exists():
            logger.info("cli.success", video_path=str(job.output_video))
            print(f"\n✅ Video successfully generated at: {job.output_video}")
            if job.output_subtitle:
                print(f"📝 Subtitles available at: {job.output_subtitle}")
            return 0
        else:
            logger.error("cli.failed", error=job.error_message)
            print(f"\n❌ Pipeline failed: {job.error_message}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user.")
        return 130
    except Exception as e:
        logger.exception("cli.fatal_error")
        print(f"\n❌ Fatal error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
