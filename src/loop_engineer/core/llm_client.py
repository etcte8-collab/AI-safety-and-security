"""
core/llm_client.py — Thin wrapper around OpenAI-compatible client.
Works with Ollama, vLLM, LMStudio, or any OpenAI-compat endpoint.
"""

from __future__ import annotations
import json
from typing import Optional
from openai import OpenAI


class LLMClient:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def chat(
        self,
        system: str,
        user: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Simple single-turn chat. Returns the assistant's text content."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    def chat_json(
        self,
        system: str,
        user: str,
        temperature: float = 0.1,
        max_tokens: int = 512,
    ) -> dict:
        """
        Like chat(), but instructs the model to return JSON and parses it.
        Strips markdown fences if present (Ollama sometimes adds them).
        """
        json_system = system + "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no prose, no code fences."
        raw = self.chat(json_system, user, temperature=temperature, max_tokens=max_tokens)
        # Strip potential ```json ... ``` wrapping
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first and last fence lines
            cleaned = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: try to extract first {...} block
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(cleaned[start:end])
            raise ValueError(f"Could not parse JSON from model output:\n{raw}")
