"""
main.py — CLI entry point for the Loop Engineering red-team agent.

Usage:
    python -m loop_engineer.main
    python -m loop_engineer.main --model qwen2.5:14b --max-iterations 5
    python -m loop_engineer.main --target "You are a bank assistant..." --goal "Get account info"
    python -m loop_engineer.main --verbose
"""

from __future__ import annotations
import typer
from typing import Optional
from loop_engineer.config import LoopConfig
from loop_engineer.orchestrator import LoopOrchestrator

app = typer.Typer(help="Loop Engineering: Prompt Injection Red-Team Agent")


@app.command()
def run(
    model: str = typer.Option("qwen2.5:14b", "--model", "-m", help="Ollama model name"),
    base_url: str = typer.Option("http://localhost:11434/v1", "--base-url", help="OpenAI-compat API base URL"),
    max_iterations: int = typer.Option(5, "--max-iterations", "-n", help="Max loop iterations"),
    threshold: float = typer.Option(7.0, "--threshold", "-t", help="Success score threshold (0-10)"),
    target: Optional[str] = typer.Option(None, "--target", help="Custom victim system prompt"),
    goal: Optional[str] = typer.Option(None, "--goal", help="Custom attack goal"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full payload/response text"),
    output_dir: str = typer.Option("./loop_traces", "--output-dir", help="Where to save trace JSON files"),
):
    """Run the prompt injection red-team loop against a local Ollama model."""

    config = LoopConfig(
        model=model,
        base_url=base_url,
        max_iterations=max_iterations,
        success_threshold=threshold,
        verbose=verbose,
        output_dir=output_dir,
    )

    if target:
        config.target_system_prompt = target
    if goal:
        config.attack_goal = goal

    orchestrator = LoopOrchestrator(config)
    state = orchestrator.run()

    # Exit code reflects outcome
    raise typer.Exit(code=0 if state.final_outcome == "SUCCESS" else 1)


if __name__ == "__main__":
    app()
