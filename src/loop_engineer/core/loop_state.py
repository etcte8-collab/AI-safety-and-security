"""
core/loop_state.py — Shared mutable state passed through every loop iteration.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class IterationRecord:
    """One full pass through Generator → Attacker → Evaluator → Judge."""
    iteration: int
    payload: str
    victim_response: str
    score: float
    score_reasoning: str
    judge_decision: str          # "SUCCESS" | "RETRY" | "ABORT"
    judge_feedback: str          # Passed back to Generator on next iter
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class LoopState:
    """
    Central state object mutated as the loop progresses.
    The orchestrator creates one instance and hands it to each agent in sequence.
    """
    # Static context
    target_system_prompt: str = ""
    attack_goal: str = ""

    # Dynamic state
    current_iteration: int = 0
    history: list[IterationRecord] = field(default_factory=list)
    last_payload: Optional[str] = None
    last_victim_response: Optional[str] = None
    last_score: float = 0.0
    last_feedback: str = ""         # Generator reads this on retry

    # Terminal state
    finished: bool = False
    final_outcome: str = ""         # "SUCCESS" | "MAX_ITER" | "ABORT"
    best_score: float = 0.0
    best_payload: Optional[str] = None

    def record(self, record: IterationRecord) -> None:
        self.history.append(record)
        if record.score > self.best_score:
            self.best_score = record.score
            self.best_payload = record.payload

    def summary(self) -> dict:
        return {
            "iterations": self.current_iteration,
            "best_score": self.best_score,
            "best_payload": self.best_payload,
            "final_outcome": self.final_outcome,
            "history": [
                {
                    "iter": r.iteration,
                    "score": r.score,
                    "decision": r.judge_decision,
                    "payload_preview": r.payload[:80] + "..." if len(r.payload) > 80 else r.payload,
                }
                for r in self.history
            ],
        }
