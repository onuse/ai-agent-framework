"""
LLM Client Abstraction Layer

Provides a unified interface for both Ollama and OpenAI-compatible API servers.
This allows the framework to work with either local Ollama or remote OpenAI-compatible servers.
"""

from typing import Dict, Any, List, Optional
import os


class LLMClient:
    """Unified LLM client supporting Ollama and OpenAI-compatible APIs."""

    def __init__(
        self,
        provider: str = "openai",
        model: str = "llama3.1:8b",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        extract_final_answer: bool = True,
        final_answer_marker: str = "<|start|>assistant<|channel|>final<|message|>"
    ):
        """
        Initialize LLM client.

        Args:
            provider: "ollama" or "openai" (default: "openai")
            model: Model name to use
            api_key: API key (not needed for Ollama, optional for OpenAI-compatible)
            base_url: Base URL for API (required for OpenAI-compatible servers)
            extract_final_answer: Whether to extract final answer from reasoning models (default: True)
            final_answer_marker: Marker that indicates start of final answer in reasoning models
        """
        self.provider = provider.lower()
        self.model = model
        self.extract_final_answer = extract_final_answer
        self.final_answer_marker = final_answer_marker

        if self.provider == "openai":
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. Install with: pip install openai"
                )

            # Initialize OpenAI client (works with OpenAI-compatible servers)
            self.client = OpenAI(
                api_key=api_key or os.getenv("OPENAI_API_KEY", "not-needed"),
                base_url=base_url or os.getenv("OPENAI_BASE_URL")
            )

        elif self.provider == "ollama":
            try:
                import ollama
            except ImportError:
                raise ImportError(
                    "Ollama package not installed. Install with: pip install ollama"
                )

            self.client = ollama

        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'ollama' or 'openai'")

    def _extract_final_answer_from_reasoning(self, content: str) -> str:
        """
        Extract final answer from reasoning model output.

        Reasoning models (like GPT-OSS:120b) output their entire chain of thought,
        with the final answer marked by a special marker. This method extracts
        only the final answer portion.

        Args:
            content: Full response content including reasoning

        Returns:
            Final answer content (or original content if marker not found)
        """
        if not self.extract_final_answer or not self.final_answer_marker:
            return content

        # Check if the marker exists in the content
        if self.final_answer_marker in content:
            # Extract everything after the marker
            marker_pos = content.find(self.final_answer_marker)
            final_answer = content[marker_pos + len(self.final_answer_marker):].strip()

            # Some models may have additional markers at the end, clean them up
            # Remove common end markers like <|end|> or similar
            for end_marker in ["<|end|>", "<|endoftext|>", "<|eot_id|>"]:
                if end_marker in final_answer:
                    final_answer = final_answer.split(end_marker)[0].strip()

            return final_answer

        # If marker not found, return original content
        return content

    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Dict with 'message' key containing 'content' (Ollama-compatible format)
        """
        if self.provider == "openai":
            # Call OpenAI-compatible API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )

            # Get raw content
            raw_content = response.choices[0].message.content

            # Extract final answer from reasoning models if needed
            final_content = self._extract_final_answer_from_reasoning(raw_content)

            # Return in Ollama-compatible format for backward compatibility
            return {
                'message': {
                    'content': final_content,
                    'role': response.choices[0].message.role
                },
                'model': response.model,
                'created_at': getattr(response, 'created', None),
                'reasoning_extracted': raw_content != final_content  # Flag to indicate extraction happened
            }

        else:  # ollama
            # Call Ollama API (already in the right format)
            response = self.client.chat(
                model=self.model,
                messages=messages,
                **kwargs
            )

            # Extract final answer from reasoning models if needed
            if 'message' in response and 'content' in response['message']:
                raw_content = response['message']['content']
                final_content = self._extract_final_answer_from_reasoning(raw_content)
                response['message']['content'] = final_content
                response['reasoning_extracted'] = raw_content != final_content

            return response

    def __repr__(self):
        return f"LLMClient(provider='{self.provider}', model='{self.model}')"
