"""
agents/generator.py — Payload Generator Agent.

Generates adversarial prompt injection payloads.
On retry iterations, incorporates feedback from the Evaluator/Judge.
"""

from __future__ import annotations
from loop_engineer.core.llm_client import LLMClient
from loop_engineer.core.loop_state import LoopState
from loop_engineer.utils.prompts import GENERATOR_SYSTEM, GENERATOR_USER
from loop_engineer.config import LoopConfig


class GeneratorAgent:
    """
    Generates prompt injection payloads.

    Loop Engineering pattern: on each retry, the feedback from the
    previous Evaluator+Judge cycle is injected into the user prompt,
    steering the generator toward more effective techniques.
    """

    def __init__(self, client: LLMClient, config: LoopConfig):
        self.client = client
        self.config = config

    def generate(self, state: LoopState) -> str:
        """
        Generate one payload. Uses state.last_feedback from previous iteration.
        Returns the raw payload string.
        """
        # Build context about target from what we know
        target_context = (
            f"Goal: {state.attack_goal}\n"
            f"Known/inferred: The target likely has restrictions around revealing its system prompt."
        )

        # On first iteration, no feedback yet
        feedback = state.last_feedback or (
            "This is the first attempt. Try a direct, classic approach first to establish a baseline."
        )

        user_prompt = GENERATOR_USER.format(
            attack_goal=state.attack_goal,
            target_context=target_context,
            feedback=feedback,
            iteration=state.current_iteration,
            max_iterations=self.config.max_iterations,
        )

        payload = self.client.chat(
            system=GENERATOR_SYSTEM,
            user=user_prompt,
            temperature=self.config.temperature_generator,
            max_tokens=512,
        )
        return payload.strip()
