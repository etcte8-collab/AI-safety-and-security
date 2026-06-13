"""
agents/retry_judge.py — Convergence / Retry Judge Agent.

This agent decides whether to:
  - SUCCESS: Stop the loop — attack threshold met
  - RETRY:   Continue with refined strategy
  - ABORT:   Early exit — attack vector exhausted

The Judge also generates specific feedback for the Generator on the next iteration.
This feedback → Generator injection is the core of the "loop engineering" pattern.
"""

from __future__ import annotations
from dataclasses import dataclass
from loop_engineer.core.llm_client import LLMClient
from loop_engineer.core.loop_state import LoopState
from loop_engineer.agents.evaluator import EvaluationResult
from loop_engineer.utils.prompts import JUDGE_SYSTEM, JUDGE_USER
from loop_engineer.config import LoopConfig


@dataclass
class JudgeDecision:
    decision: str          # "SUCCESS" | "RETRY" | "ABORT"
    feedback: str          # For Generator next iteration
    reasoning: str


class RetryJudgeAgent:
    """
    Controls loop convergence.

    Loop Engineering pattern:
    - Hard rule: if iteration >= max_iterations → ABORT regardless of score
    - Hard rule: if score >= threshold → SUCCESS regardless of judge opinion
    - Otherwise: LLM judge decides RETRY vs early ABORT based on trend
    """

    def __init__(self, client: LLMClient, config: LoopConfig):
        self.client = client
        self.config = config

    def decide(
        self,
        state: LoopState,
        eval_result: EvaluationResult,
    ) -> JudgeDecision:
        """
        Evaluate whether to continue the loop.
        Returns a JudgeDecision with the verdict and feedback for next iteration.
        """
        # Hard rule: success threshold met
        if eval_result.score >= self.config.success_threshold:
            return JudgeDecision(
                decision="SUCCESS",
                feedback="Attack succeeded — no further iterations needed.",
                reasoning=f"Score {eval_result.score:.1f} meets threshold {self.config.success_threshold}",
            )

        # Hard rule: max iterations reached
        if state.current_iteration >= self.config.max_iterations:
            return JudgeDecision(
                decision="ABORT",
                feedback="Max iterations reached.",
                reasoning="Loop exhausted all iterations without meeting success threshold.",
            )

        # Score history for trend analysis
        score_history = [r.score for r in state.history]

        user_prompt = JUDGE_USER.format(
            iteration=state.current_iteration,
            max_iterations=self.config.max_iterations,
            score=eval_result.score,
            threshold=self.config.success_threshold,
            score_history=score_history,
            reasoning=eval_result.reasoning,
            recommended_technique=eval_result.recommended_technique,
        )

        try:
            result = self.client.chat_json(
                system=JUDGE_SYSTEM,
                user=user_prompt,
                temperature=self.config.temperature_judge,
            )

            decision = result.get("decision", "RETRY").upper()
            if decision not in ("SUCCESS", "RETRY", "ABORT"):
                decision = "RETRY"

            return JudgeDecision(
                decision=decision,
                feedback=result.get("feedback_for_generator", eval_result.recommended_technique),
                reasoning=result.get("reasoning", ""),
            )

        except (ValueError, KeyError):
            # Fallback: just retry with evaluator's suggestion
            return JudgeDecision(
                decision="RETRY",
                feedback=eval_result.recommended_technique or "Try a different technique.",
                reasoning="Judge parse error — defaulting to RETRY",
            )
