"""
Configuration for AI Agent Framework

This file contains settings for LLM provider, model, and API configuration.
"""

import os

# LLM Provider Configuration
# Options: "openai" (for OpenAI-compatible servers) or "ollama" (for local Ollama)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

# Model Configuration
# For OpenAI-compatible: Use model name supported by your server
# For Ollama: Use locally available model (e.g., "llama3.1:8b")
# Current server has: gpt-oss:120b (reasoning model), whisper-large-v3
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-oss:120b")

# OpenAI-Compatible API Configuration
# Base URL for your OpenAI-compatible API server
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://192.168.1.95:8000/v1")

# API Key (use "not-needed" if your server doesn't require authentication)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "not-needed")

# Ollama Configuration (used when LLM_PROVIDER = "ollama")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Reasoning Model Configuration
# Some models (like GPT-OSS:120b) output their full chain of thought and mark the
# final answer with a special marker. Enable extraction to get only the final answer.
EXTRACT_FINAL_ANSWER = os.getenv("EXTRACT_FINAL_ANSWER", "true").lower() == "true"
FINAL_ANSWER_MARKER = os.getenv(
    "FINAL_ANSWER_MARKER",
    "<|start|>assistant<|channel|>final<|message|>"
)


def get_llm_config():
    """
    Get LLM configuration based on current settings.

    Returns:
        Dict with configuration for LLMClient initialization
    """
    config = {
        "provider": LLM_PROVIDER,
        "model": LLM_MODEL,
        "extract_final_answer": EXTRACT_FINAL_ANSWER,
        "final_answer_marker": FINAL_ANSWER_MARKER,
    }

    if LLM_PROVIDER == "openai":
        config["base_url"] = OPENAI_BASE_URL
        config["api_key"] = OPENAI_API_KEY

    return config


def print_config():
    """Print current configuration for debugging."""
    print("=" * 60)
    print("AI Agent Framework - LLM Configuration")
    print("=" * 60)
    print(f"Provider: {LLM_PROVIDER}")
    print(f"Model: {LLM_MODEL}")

    if LLM_PROVIDER == "openai":
        print(f"Base URL: {OPENAI_BASE_URL}")
        print(f"API Key: {'*' * 8 if OPENAI_API_KEY != 'not-needed' else 'not-needed'}")
    else:
        print(f"Ollama Host: {OLLAMA_HOST}")

    print(f"\nReasoning Model Settings:")
    print(f"Extract Final Answer: {EXTRACT_FINAL_ANSWER}")
    if EXTRACT_FINAL_ANSWER:
        print(f"Final Answer Marker: {FINAL_ANSWER_MARKER[:50]}...")

    print("=" * 60)


if __name__ == "__main__":
    # Print configuration when run directly
    print_config()
