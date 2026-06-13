"""
orchestrator.py — The main Loop Orchestrator.

Wires together: Generator → Attacker → Evaluator → Judge → (repeat)

This is the heart of the "Loop Engineering" pattern:
each agent's output feeds into the next, and the Judge's feedback
closes the loop back to the Generator.
"""

from __future__ import annotations
from loop_engineer.config import LoopConfig
from loop_engineer.core.llm_client import LLMClient
from loop_engineer.core.loop_state import LoopState, IterationRecord
from loop_engineer.agents.generator import GeneratorAgent
from loop_engineer.agents.attacker import AttackerAgent
from loop_engineer.agents.evaluator import EvaluatorAgent
from loop_engineer.agents.retry_judge import RetryJudgeAgent
from loop_engineer.core import tracer


class LoopOrchestrator:
    """
    Runs the Generator → Attacker → Evaluator → Judge loop.

    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │GENERATOR │───►│ ATTACKER │───►│EVALUATOR │───►│  JUDGE   │
    └──────────┘    └──────────┘    └──────────┘    └────┬─────┘
         ▲                                               │
         └──────────────── feedback ◄───────────────────┘
    """

    def __init__(self, config: LoopConfig):
        self.config = config
        client = LLMClient(
            base_url=config.base_url,
            api_key=config.api_key,
            model=config.model,
        )
        self.generator = GeneratorAgent(client, config)
        self.attacker = AttackerAgent(client, config)
        self.evaluator = EvaluatorAgent(client, config)
        self.judge = RetryJudgeAgent(client, config)

    def run(self) -> LoopState:
        """Execute the full loop. Returns final LoopState."""
        state = LoopState(
            target_system_prompt=self.config.target_system_prompt,
            attack_goal=self.config.attack_goal,
        )

        tracer.print_header({
            "model": self.config.model,
            "max_iterations": self.config.max_iterations,
            "success_threshold": self.config.success_threshold,
            "attack_goal": self.config.attack_goal,
        })

        while not state.finished:
            state.current_iteration += 1
            tracer.print_iteration_start(state.current_iteration, self.config.max_iterations)

            # ── Step 1: Generator ──────────────────────────────────────────
            payload = self.generator.generate(state)
            state.last_payload = payload
            if self.config.verbose:
                tracer.print_agent_output("Generator", payload, color="cyan")
            else:
                tracer.print_agent_output(
                    "Generator",
                    payload[:100] + "..." if len(payload) > 100 else payload,
                    color="cyan",
                )

            # ── Step 2: Attacker (Victim Simulator) ────────────────────────
            victim_response = self.attacker.respond(state, payload)
            state.last_victim_response = victim_response
            tracer.print_agent_output(
                "Victim",
                victim_response[:150] + "..." if len(victim_response) > 150 else victim_response,
                color="magenta",
            )

            # ── Step 3: Evaluator ──────────────────────────────────────────
            eval_result = self.evaluator.evaluate(state, payload, victim_response)
            state.last_score = eval_result.score
            tracer.print_score(eval_result.score, eval_result.reasoning)

            # ── Step 4: Retry Judge ────────────────────────────────────────
            judge_decision = self.judge.decide(state, eval_result)
            state.last_feedback = judge_decision.feedback
            tracer.print_judge(judge_decision.decision, judge_decision.feedback)

            # ── Record this iteration ──────────────────────────────────────
            record = IterationRecord(
                iteration=state.current_iteration,
                payload=payload,
                victim_response=victim_response,
                score=eval_result.score,
                score_reasoning=eval_result.reasoning,
                judge_decision=judge_decision.decision,
                judge_feedback=judge_decision.feedback,
            )
            state.record(record)

            # ── Check terminal conditions ──────────────────────────────────
            if judge_decision.decision in ("SUCCESS", "ABORT"):
                state.finished = True
                state.final_outcome = judge_decision.decision
            elif state.current_iteration >= self.config.max_iterations:
                state.finished = True
                state.final_outcome = "MAX_ITER"

        # ── Print and save results ─────────────────────────────────────────
        tracer.print_final_summary(state)
        tracer.save_trace(state, self.config.output_dir)

        return state
