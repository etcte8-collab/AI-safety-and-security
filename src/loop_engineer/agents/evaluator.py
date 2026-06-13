"""
agents/evaluator.py — Attack Success Evaluator Agent.

Scores how well the injection payload succeeded at achieving the attack goal.
Outputs structured JSON with a score and reasoning.

This is the key feedback signal that drives the loop's learning.
"""

from __future__ import annotations
from dataclasses import dataclass
from loop_engineer.core.llm_client import LLMClient
from loop_engineer.core.loop_state import LoopState
from loop_engineer.utils.prompts import EVALUATOR_SYSTEM, EVALUATOR_USER
from loop_engineer.config import LoopConfig


@dataclass
class EvaluationResult:
    score: float
    success_indicators: list[str]
    defense_indicators: list[str]
    reasoning: str
    recommended_technique: str


class EvaluatorAgent:
    """
    Evaluates how successful the attack payload was.

    Loop Engineering pattern:
    - Uses structured JSON output (score + reasoning + technique recommendation)
    - The recommendation flows into Judge → Generator on the next iteration
    - Low temperature ensures consistent, deterministic scoring
    """

    def __init__(self, client: LLMClient, config: LoopConfig):
        self.client = client
        self.config = config

    def evaluate(self, state: LoopState, payload: str, victim_response: str) -> EvaluationResult:
        """
        Score the attack. Returns an EvaluationResult with structured data.
        """
        user_prompt = EVALUATOR_USER.format(
            attack_goal=state.attack_goal,
            payload=payload,
            victim_response=victim_response,
        )

        try:
            result = self.client.chat_json(
                system=EVALUATOR_SYSTEM,
                user=user_prompt,
                temperature=self.config.temperature_evaluator,
            )

            return EvaluationResult(
                score=float(result.get("score", 0.0)),
                success_indicators=result.get("success_indicators", []),
                defense_indicators=result.get("defense_indicators", []),
                reasoning=result.get("reasoning", ""),
                recommended_technique=result.get("recommended_technique", ""),
            )

        except (ValueError, KeyError) as e:
            # Graceful degradation: if JSON parse fails, return neutral score
            return EvaluationResult(
                score=0.0,
                success_indicators=[],
                defense_indicators=["JSON parse error in evaluator"],
                reasoning=f"Evaluator error: {e}",
                recommended_technique="Try again",
            )
