"""
core/tracer.py — Rich-powered loop execution tracer.
Prints a live audit trail of each iteration; also saves JSON trace to disk.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from loop_engineer.core.loop_state import IterationRecord, LoopState

console = Console()


def _score_color(score: float) -> str:
    if score >= 8:
        return "bold red"
    elif score >= 5:
        return "yellow"
    else:
        return "green"


def print_header(config_summary: dict) -> None:
    console.print(Panel(
        f"[bold cyan]🔁 Loop Engineering — Prompt Injection Red-Team[/bold cyan]\n"
        f"Model: [yellow]{config_summary.get('model')}[/yellow]  "
        f"Max Iterations: [yellow]{config_summary.get('max_iterations')}[/yellow]  "
        f"Success Threshold: [yellow]{config_summary.get('success_threshold')}[/yellow]\n\n"
        f"[dim]Attack Goal:[/dim] {config_summary.get('attack_goal')}",
        border_style="cyan",
        expand=False,
    ))


def print_iteration_start(iteration: int, max_iter: int) -> None:
    console.rule(f"[bold blue]Iteration {iteration}/{max_iter}[/bold blue]")


def print_agent_output(agent_name: str, content: str, color: str = "white") -> None:
    label = f"[bold {color}][{agent_name}][/bold {color}]"
    # Truncate long content for display
    display = content if len(content) <= 300 else content[:300] + "[dim]...[/dim]"
    console.print(f"  {label} {display}")


def print_score(score: float, reasoning: str) -> None:
    color = _score_color(score)
    console.print(f"  [bold][Evaluator][/bold] Score: [{color}]{score:.1f}/10[/{color}] — {reasoning[:120]}")


def print_judge(decision: str, feedback: str) -> None:
    icons = {"SUCCESS": "✅", "RETRY": "🔄", "ABORT": "🛑"}
    colors = {"SUCCESS": "bold green", "RETRY": "bold yellow", "ABORT": "bold red"}
    icon = icons.get(decision, "❓")
    color = colors.get(decision, "white")
    console.print(f"  [bold][Judge][/bold] {icon} [{color}]{decision}[/{color}] — {feedback[:120]}")


def print_final_summary(state: LoopState) -> None:
    outcome_color = "green" if state.final_outcome == "SUCCESS" else "yellow"
    console.print()
    console.print(Panel(
        f"[bold]Final Outcome:[/bold] [{outcome_color}]{state.final_outcome}[/{outcome_color}]\n"
        f"[bold]Iterations:[/bold] {state.current_iteration}\n"
        f"[bold]Best Score:[/bold] [{_score_color(state.best_score)}]{state.best_score:.1f}/10[/{_score_color(state.best_score)}]\n"
        f"[bold]Best Payload:[/bold]\n[italic]{state.best_payload}[/italic]",
        title="📊 Loop Summary",
        border_style=outcome_color,
    ))

    # History table
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    table.add_column("Iter", style="dim", width=5)
    table.add_column("Score", width=8)
    table.add_column("Decision", width=10)
    table.add_column("Payload Preview", no_wrap=False)

    for r in state.history:
        color = _score_color(r.score)
        table.add_row(
            str(r.iteration),
            f"[{color}]{r.score:.1f}[/{color}]",
            r.judge_decision,
            r.payload[:60] + "..." if len(r.payload) > 60 else r.payload,
        )
    console.print(table)


def save_trace(state: LoopState, output_dir: str) -> str:
    """Save full loop trace as JSON."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"trace_{ts}.json")
    with open(path, "w") as f:
        # Serialize history records
        data = {
            "attack_goal": state.attack_goal,
            "target_system_prompt": state.target_system_prompt,
            "final_outcome": state.final_outcome,
            "best_score": state.best_score,
            "best_payload": state.best_payload,
            "iterations": state.current_iteration,
            "history": [vars(r) for r in state.history],
        }
        json.dump(data, f, indent=2)
    console.print(f"\n[dim]Trace saved → {path}[/dim]")
    return path
