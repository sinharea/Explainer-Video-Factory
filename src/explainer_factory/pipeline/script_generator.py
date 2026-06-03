"""Educational script generation pipeline.

Generates structured educational scripts for complex topics.
Supports both template-based (offline) and LLM-powered generation.
"""

from __future__ import annotations

from explainer_factory.exceptions import ScriptGenerationError
from explainer_factory.logging import get_logger
from explainer_factory.models.script import DifficultyLevel, Script, ScriptSegment

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────
# Pre-authored educational content templates
# ─────────────────────────────────────────────────────────────────────

TOPIC_TEMPLATES: dict[str, dict] = {
    "quantum entanglement": {
        "title": "Quantum Entanglement: The Spooky Connection",
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "summary": (
            "An exploration of quantum entanglement — one of the most "
            "fascinating phenomena in physics, where particles become "
            "mysteriously linked across any distance."
        ),
        "keywords": [
            "quantum entanglement",
            "superposition",
            "EPR paradox",
            "Bell's theorem",
            "quantum states",
            "wave function",
            "measurement",
            "spooky action",
        ],
        "segments": [
            {
                "text": (
                    "Welcome to this exploration of one of the most mind-bending "
                    "concepts in modern physics: Quantum Entanglement."
                ),
                "emphasis": True,
                "pause_after": 0.8,
            },
            {
                "text": (
                    "Imagine you have two coins that are magically linked. "
                    "No matter how far apart they are, when you flip one and it lands "
                    "on heads, the other instantly lands on tails. "
                    "This is a simplified analogy for quantum entanglement."
                ),
                "pause_after": 0.6,
            },
            {
                "text": (
                    "In the quantum world, particles like electrons and photons "
                    "can exist in a state called superposition. "
                    "This means they don't have a definite property "
                    "until they are measured."
                ),
                "pause_after": 0.5,
            },
            {
                "text": (
                    "When two particles become entangled, their quantum states "
                    "become linked. Measuring one particle instantly determines "
                    "the state of the other, regardless of the distance between them."
                ),
                "emphasis": True,
                "pause_after": 0.6,
            },
            {
                "text": (
                    "Einstein famously called this 'spooky action at a distance' "
                    "because it seemed to violate the principle that nothing can "
                    "travel faster than light."
                ),
                "pause_after": 0.5,
            },
            {
                "text": (
                    "In 1935, Einstein, Podolsky, and Rosen proposed a thought "
                    "experiment known as the EPR paradox. They argued that quantum "
                    "mechanics must be incomplete, suggesting hidden variables "
                    "must explain these correlations."
                ),
                "pause_after": 0.6,
            },
            {
                "text": (
                    "However, in 1964, physicist John Bell developed a mathematical "
                    "inequality, known as Bell's theorem. This provided a way to "
                    "experimentally test whether hidden variables could explain "
                    "quantum entanglement."
                ),
                "pause_after": 0.5,
            },
            {
                "text": (
                    "Experiments conducted by Alain Aspect in 1982 and many others "
                    "since then have consistently violated Bell's inequality. "
                    "This confirms that quantum entanglement is real and cannot "
                    "be explained by hidden variables."
                ),
                "emphasis": True,
                "pause_after": 0.6,
            },
            {
                "text": (
                    "So how does entanglement actually work at a technical level? "
                    "When particles interact, they can form a combined quantum state "
                    "described by a single wave function. This entangled state "
                    "cannot be described independently for each particle."
                ),
                "pause_after": 0.5,
            },
            {
                "text": (
                    "Today, quantum entanglement has practical applications. "
                    "It forms the backbone of quantum computing, where entangled "
                    "qubits can process information exponentially faster than "
                    "classical bits."
                ),
                "pause_after": 0.5,
            },
            {
                "text": (
                    "Quantum cryptography uses entanglement to create "
                    "theoretically unbreakable encryption. Any attempt to "
                    "eavesdrop on an entangled communication channel "
                    "would disturb the quantum states and be detected."
                ),
                "pause_after": 0.5,
            },
            {
                "text": (
                    "Researchers are also exploring quantum teleportation, "
                    "which uses entanglement to transfer quantum information "
                    "between distant locations. While it doesn't teleport matter, "
                    "it transfers quantum states perfectly."
                ),
                "pause_after": 0.6,
            },
            {
                "text": (
                    "To summarize: quantum entanglement is a fundamental feature "
                    "of quantum mechanics where particles share correlated states "
                    "instantaneously across any distance. It has been experimentally "
                    "verified and is driving revolutionary technologies."
                ),
                "emphasis": True,
                "pause_after": 0.5,
            },
            {
                "text": (
                    "Thank you for exploring quantum entanglement with us. "
                    "The quantum world continues to surprise and challenge "
                    "our understanding of reality."
                ),
                "pause_after": 1.0,
            },
        ],
    },
}

# Fallback template for unknown topics
DEFAULT_TEMPLATE_SEGMENTS = [
    {
        "text": "Welcome to this educational exploration of {topic}.",
        "emphasis": True,
        "pause_after": 0.8,
    },
    {
        "text": (
            "{topic} is a fascinating subject that has captured the attention "
            "of scientists, researchers, and curious minds around the world."
        ),
        "pause_after": 0.5,
    },
    {
        "text": (
            "Let's begin by understanding the fundamental concepts. "
            "At its core, {topic} involves complex interactions and principles "
            "that shape our understanding of the world."
        ),
        "pause_after": 0.5,
    },
    {
        "text": (
            "The key principles behind {topic} were developed through decades "
            "of careful research and experimentation by scientists worldwide."
        ),
        "pause_after": 0.5,
    },
    {
        "text": (
            "One of the most important aspects of {topic} is how it connects "
            "to practical applications in technology, medicine, and engineering."
        ),
        "pause_after": 0.5,
    },
    {
        "text": (
            "Modern research continues to push the boundaries of {topic}, "
            "opening new possibilities that were previously unimaginable."
        ),
        "pause_after": 0.5,
    },
    {
        "text": (
            "In conclusion, {topic} represents a critical area of knowledge "
            "with far-reaching implications for science and technology. "
            "Thank you for joining this exploration."
        ),
        "emphasis": True,
        "pause_after": 1.0,
    },
]


class ScriptGenerator:
    """Generates educational scripts from topics.

    Uses template-based generation by default, with optional LLM
    integration for higher quality, topic-adaptive scripts.
    """

    def __init__(self, use_llm: bool = False):
        """Initialize the script generator.

        Args:
            use_llm: Whether to use LLM for generation (requires API key).
        """
        self.use_llm = use_llm
        logger.info("script_generator.init", use_llm=use_llm)

    def generate(
        self,
        topic: str,
        difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
        target_duration: float = 120.0,
    ) -> Script:
        """Generate an educational script for the given topic.

        Args:
            topic: The educational topic to generate content for.
            difficulty: Target difficulty level.
            target_duration: Target video duration in seconds.

        Returns:
            A structured Script object with segmented narration.

        Raises:
            ScriptGenerationError: If script generation fails.
        """
        logger.info(
            "script_generator.generate",
            topic=topic,
            difficulty=difficulty.value,
            target_duration=target_duration,
        )

        try:
            if self.use_llm:
                return self._generate_with_llm(topic, difficulty, target_duration)
            return self._generate_from_template(topic, difficulty, target_duration)
        except Exception as e:
            raise ScriptGenerationError(
                f"Failed to generate script for topic '{topic}'",
                details={"topic": topic, "error": str(e)},
            ) from e

    def _generate_from_template(
        self,
        topic: str,
        difficulty: DifficultyLevel,
        target_duration: float,
    ) -> Script:
        """Generate script using pre-authored templates."""
        topic_key = topic.lower().strip()

        # Check for exact or partial match in templates
        template = None
        for key, tmpl in TOPIC_TEMPLATES.items():
            if key in topic_key or topic_key in key:
                template = tmpl
                break

        if template:
            logger.info("script_generator.template_match", topic=topic)
            segments = [ScriptSegment(**seg) for seg in template["segments"]]
            return Script(
                topic=topic,
                title=template["title"],
                difficulty=template.get("difficulty", difficulty),
                summary=template["summary"],
                segments=segments,
                keywords=template["keywords"],
                target_duration=target_duration,
            )

        # Fallback: generate from default template with topic substitution
        logger.info("script_generator.fallback_template", topic=topic)
        segments = []
        for seg_data in DEFAULT_TEMPLATE_SEGMENTS:
            seg = ScriptSegment(
                text=seg_data["text"].format(topic=topic),
                emphasis=seg_data.get("emphasis", False),
                pause_after=seg_data.get("pause_after", 0.3),
            )
            segments.append(seg)

        return Script(
            topic=topic,
            title=f"Understanding {topic}",
            difficulty=difficulty,
            summary=f"An educational exploration of {topic}.",
            segments=segments,
            keywords=[topic.lower()],
            target_duration=target_duration,
        )

    def _generate_with_llm(
        self,
        topic: str,
        difficulty: DifficultyLevel,
        target_duration: float,
    ) -> Script:
        """Generate script using LLM (requires API keys).

        This is a placeholder for LLM integration. When enabled,
        it would use LangChain to generate adaptive, topic-specific
        educational content.
        """
        # TODO: Implement LangChain-based generation when LLM keys are available
        logger.warning(
            "script_generator.llm_fallback",
            msg="LLM generation not configured, falling back to templates",
        )
        return self._generate_from_template(topic, difficulty, target_duration)
