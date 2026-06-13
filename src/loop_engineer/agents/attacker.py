"""
agents/attacker.py — Victim Model Simulator (the "Attacker" step).

This agent simulates the target/victim LLM receiving the injection payload.
It responds as that model would, given its system prompt constraints.

In a real deployment this would be an actual API call to the target system.
Here, we simulate it locally for safe red-team research.
"""

from __future__ import annotations
from loop_engineer.core.llm_client import LLMClient
from loop_engineer.core.loop_state import LoopState
from loop_engineer.utils.prompts import ATTACKER_SYSTEM_TEMPLATE, ATTACKER_USER_TEMPLATE
from loop_engineer.config import LoopConfig


class AttackerAgent:
    """
    Simulates the victim LLM's response to an injection payload.

    The victim's system prompt is injected into this agent's system message,
    making it role-play as the constrained model.

    Loop Engineering note: this agent has no loop-iteration dependency —
    it always just responds to the current payload with the same system prompt.
    The loop learning happens in Generator ↔ Evaluator ↔ Judge.
    """

    def __init__(self, client: LLMClient, config: LoopConfig):
        self.client = client
        self.config = config

    def respond(self, state: LoopState, payload: str) -> str:
        """
        Simulate the victim model responding to the payload.
        Returns the victim's response string.
        """
        system = ATTACKER_SYSTEM_TEMPLATE.format(
            target_system_prompt=state.target_system_prompt
        )
        user = ATTACKER_USER_TEMPLATE.format(payload=payload)

        response = self.client.chat(
            system=system,
            user=user,
            temperature=self.config.temperature_attacker,
            max_tokens=512,
        )
        return response.strip()
