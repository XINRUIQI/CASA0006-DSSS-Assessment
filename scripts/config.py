"""
Project-wide configuration: paths, API tokens, time window, and filtering rules.
"""

from pathlib import Path
import os

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW      = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_OUTPUT    = PROJECT_ROOT / "data" / "output"

# ── API tokens (set via environment variables) ─────────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
HF_TOKEN     = os.getenv("HF_TOKEN", "")

# ── Time window ────────────────────────────────────────────────────────────────
TIME_START = "2022-01-01"
TIME_END   = "2025-12-31"

# ── Open-AI relevance: inclusion keywords / topics ─────────────────────────────
# Any project whose name, description, README, or tags contain at least one of
# these tokens (case-insensitive) is considered a candidate open-AI project.
AI_INCLUDE_KEYWORDS = [
    # --- general AI / ML umbrella ---
    "artificial-intelligence",
    "machine-learning",
    "deep-learning",
    "neural-network",
    "reinforcement-learning",

    # --- large language models ---
    "llm",
    "large-language-model",
    "language-model",
    "gpt",
    "chatgpt",
    "instruction-tuning",
    "fine-tuning",
    "rlhf",
    "prompt-engineering",
    "chain-of-thought",

    # --- transformer family ---
    "transformer",
    "attention-mechanism",
    "bert",
    "t5",
    "encoder-decoder",

    # --- generative AI ---
    "generative-ai",
    "text-generation",
    "code-generation",
    "image-generation",
    "text-to-image",
    "text-to-video",
    "text-to-speech",
    "text-to-audio",
    "speech-to-text",
    "image-to-text",

    # --- diffusion models ---
    "diffusion",
    "stable-diffusion",
    "diffusion-model",
    "ddpm",
    "latent-diffusion",

    # --- multimodal ---
    "multimodal",
    "vision-language",
    "clip",
    "visual-question-answering",

    # --- agents & RAG ---
    "ai-agent",
    "agent",
    "autonomous-agent",
    "rag",
    "retrieval-augmented-generation",
    "function-calling",
    "tool-use",

    # --- embeddings & vector ---
    "embedding",
    "sentence-embedding",
    "vector-database",
    "vector-search",
    "semantic-search",

    # --- NLP tasks ---
    "natural-language-processing",
    "nlp",
    "named-entity-recognition",
    "text-classification",
    "question-answering",
    "summarization",
    "translation",
    "sentiment-analysis",
    "tokenizer",

    # --- computer vision ---
    "computer-vision",
    "object-detection",
    "image-classification",
    "image-segmentation",
    "ocr",

    # --- speech & audio ---
    "speech-recognition",
    "automatic-speech-recognition",
    "asr",
    "tts",
    "voice-cloning",

    # --- open-weight / open-source model brands ---
    "open-weight",
    "open-source-model",
    "llama",
    "mistral",
    "falcon",
    "gemma",
    "phi",
    "qwen",
    "deepseek",
    "yi",
    "vicuna",
    "alpaca",
    "openchat",
    "openhermes",
    "nous-hermes",
    "whisper",
    "segment-anything",
    "chatglm",
    "glm",
    "baichuan",
    "internlm",
    "stablelm",
    "stablecode",
    "flux",
    "sam2",
    "sam3",
    "fastsam",
    "moondream",
    "dspy",
    "megatron",
    "mamba",
    "rwkv",
    "olmo",
    "arctic",
    "command-r",
    "solar",
    "jamba",

    # --- foundation / generative (broader terms) ---
    "foundation-model",
    "generative-model",
    "vision-language-model",
    "vision-model",
    "prompt",
    "context-engineering",
    "meta-prompting",
    "inpainting",
    "img2img",
    "controlnet",
    "lora",
    "adapter",

    # --- MLOps & inference ---
    "mlops",
    "model-serving",
    "model-inference",
    "quantization",
    "gguf",
    "ggml",
    "vllm",
    "tgi",
    "triton-inference",
    "onnx",
    "tensorrt",

    # --- datasets & benchmarks ---
    "ai-benchmark",
    "ai-dataset",
    "evaluation",
    "leaderboard",

    # --- robotics & embodied AI ---
    "robotics",
    "embodied-ai",
    "sim-to-real",
]

# Tokens that, if they are the *only* match, are too ambiguous on their own
# and require a second confirming keyword.
AI_WEAK_KEYWORDS = [
    "agent",
    "embedding",
    "evaluation",
    "translation",
    "tokenizer",
    "ocr",
    "robotics",
]

# Projects matching any of these patterns are excluded even if they match
# inclusion keywords (reduces false positives).
AI_EXCLUDE_KEYWORDS = [
    "awesome-list-only",
    "cheatsheet",
    "interview-questions",
    "coursework",
    "homework",
    "tutorial-only",
]

# ── Hugging Face pipeline tags considered AI-relevant ──────────────────────────
HF_AI_PIPELINE_TAGS = [
    "text-generation",
    "text2text-generation",
    "text-classification",
    "token-classification",
    "question-answering",
    "summarization",
    "translation",
    "fill-mask",
    "sentence-similarity",
    "feature-extraction",
    "zero-shot-classification",
    "conversational",
    "table-question-answering",
    "image-classification",
    "object-detection",
    "image-segmentation",
    "image-to-text",
    "text-to-image",
    "text-to-video",
    "text-to-speech",
    "text-to-audio",
    "automatic-speech-recognition",
    "audio-classification",
    "voice-activity-detection",
    "depth-estimation",
    "image-to-image",
    "unconditional-image-generation",
    "video-classification",
    "reinforcement-learning",
    "visual-question-answering",
    "document-question-answering",
    "image-text-to-text",
    "any-to-any",
]

# ── Prominence thresholds ──────────────────────────────────────────────────────
GITHUB_PROMINENCE = {
    "stars_min": 300,
    "forks_min": 30,
    "logic": "or",           # satisfy at least one
}

HF_PROMINENCE = {
    "downloads_min": 5000,
    "likes_min": 50,
    "logic": "or",
}
