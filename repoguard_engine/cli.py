"""CLI entry point: repoguard analyze | fix | gate | serve | mcp"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def main() -> None:
    """RepoGuard — AI-powered test quality guard."""


@main.command()
@click.argument("repo_path", default=".", type=click.Path(exists=True))
@click.option("--mutation", is_flag=True, default=False, help="Also run mutation testing (slow).")
@click.option("--endpoints", is_flag=True, default=False, help="Detect untested FastAPI endpoints.")
@click.option("--json-output", is_flag=True, default=False, help="Print raw JSON instead of formatted output.")
@click.option(
    "--summarize", is_flag=True, default=False,
    help="Also ask an AI provider for a plain-English summary of the measured numbers "
         "(requires credentials for the selected provider — see docs/WATSONX_SETUP.md / "
         "docs/VERTEX_SETUP.md). Advisory text only, never a source of any metric.",
)
@click.option(
    "--provider", default=None,
    help="AI provider for --summarize: 'vertex' (default) or 'watsonx'. "
         "Overrides REPOGUARD_AI_PROVIDER for this call.",
)
def analyze(repo_path: str, mutation: bool, endpoints: bool, json_output: bool, summarize: bool, provider: str | None) -> None:
    """Measure test coverage and quality gaps in REPO_PATH."""
    from .pipeline import run_pipeline

    console.print(f"[bold cyan]Analysing[/] {repo_path} …")
    result = run_pipeline(
        repo_path,
        include_mutation=mutation,
        include_endpoints=endpoints,
    )

    if json_output:
        click.echo(json.dumps(result.dashboard, indent=2))
        return

    _print_coverage_table(result)

    if summarize:
        from .narrative import generate_summary

        narrative = generate_summary(result.dashboard, provider=provider)
        if narrative.ok:
            console.print(f"\n[bold]AI summary ({narrative.provider} — advisory, not a measurement):[/]")
            console.print(narrative.text)
        else:
            console.print(f"\n[yellow]Summary unavailable:[/] {narrative.error}")


@main.command()
@click.argument("repo_path", default=".", type=click.Path(exists=True))
@click.option("--threshold", default=80.0, show_default=True, help="Coverage % gate threshold.")
def gate(repo_path: str, threshold: float) -> None:
    """CI gate: exit 1 if coverage is below THRESHOLD."""
    from .pipeline import run_pipeline

    result = run_pipeline(repo_path, gate_threshold=threshold)
    _print_coverage_table(result)

    if result.passed_gate:
        console.print(f"[bold green]✓ Gate passed[/] ({result.coverage.percent:.1f}% ≥ {threshold}%)")
    else:
        console.print(f"[bold red]✗ Gate failed[/] ({result.coverage.percent:.1f}% < {threshold}%)")
        sys.exit(1)


@main.command()
@click.argument("repo_path", default=".", type=click.Path(exists=True))
@click.option("--threshold", default=80.0, show_default=True, help="Coverage % gate threshold for the after-measurement.")
@click.option("--publish", is_flag=True, default=False, help="If the gate passes, commit tests/ to a new branch and open a PR.")
@click.option(
    "--provider", default=None,
    help="AI provider to drive the fix loop: 'vertex' (default) or 'watsonx'. "
         "Overrides REPOGUARD_AI_PROVIDER for this call.",
)
def fix(repo_path: str, threshold: float, publish: bool, provider: str | None) -> None:
    """Run the AI fix loop on REPO_PATH: measure, write tests, critique, re-measure.

    Requires credentials for the selected provider -- see docs/WATSONX_SETUP.md /
    docs/VERTEX_SETUP.md.
    """
    from .ai_providers import AIProviderError
    from .watson_agent import run_fix_loop

    console.print(f"[bold cyan]Fix loop[/] {repo_path} …")
    try:
        result = run_fix_loop(repo_path, gate_threshold=threshold, publish=publish, provider=provider)
    except AIProviderError as exc:
        console.print(f"[bold red]✗ {exc}[/]")
        sys.exit(1)
    except RuntimeError as exc:
        console.print(f"[bold red]✗ Gate failed:[/] {exc}")
        sys.exit(1)

    console.print(f"Files attempted: {', '.join(result.files_attempted) or '(none)'}")
    before = result.baseline.get("mutation") or {}
    after = (result.after or {}).get("mutation") or {}
    if before or after:
        console.print(
            f"Mutation score: {before.get('score', 'n/a')}% -> {after.get('score', 'n/a')}%"
        )
    console.print(f"Evidence: {result.evidence_path}")
    if publish:
        console.print("[bold green]PR opened[/]" if result.published else "[yellow]Gate failed — nothing published[/]")


@main.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True)
def serve(host: str, port: int) -> None:
    """Start the RepoGuard web dashboard."""
    import uvicorn
    from .web.server import app

    console.print(f"[bold green]Dashboard[/] → http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


@main.command()
def mcp() -> None:
    """Start the RepoGuard MCP server (stdio transport)."""
    from .mcp_server import mcp_app

    mcp_app.run()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_coverage_table(result) -> None:
    if not result.coverage:
        console.print("[red]No coverage data.[/]")
        return

    table = Table(title="Coverage Summary")
    table.add_column("Metric", style="bold")
    table.add_column("Value")

    cov = result.coverage
    color = "green" if cov.percent >= 80 else "yellow" if cov.percent >= 60 else "red"
    table.add_row("Coverage", f"[{color}]{cov.percent:.1f}%[/]")
    table.add_row("Covered lines", str(cov.covered_lines))
    table.add_row("Total lines", str(cov.total_lines))

    if result.gap:
        table.add_row("Files with gaps", str(len(result.gap.uncovered_files)))

    if result.mutation:
        m = result.mutation
        table.add_row("Mutation score", f"{m.score:.1f}%  ({m.killed}/{m.total} killed)")

    console.print(table)

    if result.risk:
        risk_table = Table(title="Top Risk Files")
        risk_table.add_column("File")
        risk_table.add_column("Risk Score")
        for r in result.risk[:5]:
            risk_color = "red" if r.score > 0.5 else "yellow" if r.score > 0.2 else "green"
            risk_table.add_row(r.file, f"[{risk_color}]{r.score:.3f}[/]")
        console.print(risk_table)
