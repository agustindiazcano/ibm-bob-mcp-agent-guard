"""CLI entry point: repoguard analyze | fix | gate | serve | mcp"""

from __future__ import annotations

import json
import os
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
    "--workers", default=1, show_default=True, type=click.IntRange(min=1),
    help="Run mutants on this many parallel workers (same results, less wall time).",
)
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
@click.option("--project", default=None, help="Project slug for stored runs (default: REPOGUARD_PROJECT, GITHUB_REPOSITORY, or the directory name).")
@click.option(
    "--push", "push_url", default=None, metavar="URL",
    help="Also send this run to a repoguard server's POST /api/runs (token from REPOGUARD_TOKEN). "
         "Works without the [db] extra.",
)
def analyze(
    repo_path: str, mutation: bool, endpoints: bool, json_output: bool, workers: int, summarize: bool,
    provider: str | None, project: str | None, push_url: str | None,
) -> None:
    """Measure test coverage and quality gaps in REPO_PATH.

    Stored in the run-history database too when REPOGUARD_DATABASE_URL is set.
    """
    from .mutation import NoMutantsError
    from .pipeline import run_pipeline

    token = os.environ.get("REPOGUARD_TOKEN", "")
    if push_url and not token:
        # Fail before measuring, not after a multi-minute mutation run.
        console.print("[bold red]✗ --push needs REPOGUARD_TOKEN (create one with `repoguard db create-token`).[/]")
        sys.exit(1)

    console.print(f"[bold cyan]Analysing[/] {repo_path} …")
    try:
        result = run_pipeline(
            repo_path,
            include_mutation=mutation,
            include_endpoints=endpoints,
            mutation_workers=workers,
            project=project,
            source="cli",
            build_record=bool(push_url),
        )
    except (NoMutantsError, RuntimeError) as exc:
        console.print(f"[bold red]✗ Measurement failed:[/] {exc}")
        sys.exit(1)

    if push_url:
        _push_record(push_url, token, result.record)
    if result.run_id:
        # stderr, so --json-output's stdout stays exactly the dashboard JSON.
        click.echo(f"Stored run {result.run_id}", err=True)

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
@click.option("--project", default=None, help="Project slug for stored runs (when REPOGUARD_DATABASE_URL is set).")
def gate(repo_path: str, threshold: float, project: str | None) -> None:
    """CI gate: exit 1 if coverage is below THRESHOLD."""
    from .pipeline import run_pipeline

    result = run_pipeline(repo_path, gate_threshold=threshold, project=project, source="cli")
    if result.run_id:
        click.echo(f"Stored run {result.run_id}", err=True)
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
@click.option(
    "--mutation-workers", default=1, show_default=True, type=click.IntRange(min=1),
    help="Parallel mutant workers for the before/after measurements (same numbers, less wall time).",
)
def fix(repo_path: str, threshold: float, publish: bool, provider: str | None, mutation_workers: int) -> None:
    """Run the AI fix loop on REPO_PATH: measure, write tests, critique, re-measure.

    Requires credentials for the selected provider -- see docs/WATSONX_SETUP.md /
    docs/VERTEX_SETUP.md.
    """
    from .ai_providers import AIProviderError
    from .mutation import NoMutantsError
    from .watson_agent import run_fix_loop

    console.print(f"[bold cyan]Fix loop[/] {repo_path} …")
    try:
        result = run_fix_loop(
            repo_path, gate_threshold=threshold, publish=publish, provider=provider, mutation_workers=mutation_workers
        )
    except AIProviderError as exc:
        console.print(f"[bold red]✗ {exc}[/]")
        sys.exit(1)
    except (NoMutantsError, RuntimeError) as exc:
        # Baseline guard, sham-mutant control or an empty mutation scope:
        # the loop stops rather than report a meaningless score.
        console.print(f"[bold red]✗ Measurement failed:[/] {exc}")
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


@main.group()
def db() -> None:
    """Run-history database: set up, projects and tokens (needs the [db] extra and REPOGUARD_DATABASE_URL)."""


def _store_engine():
    from . import store

    url = store.database_url()
    if url is None:
        console.print(f"[bold red]✗ {store.DATABASE_URL_ENV} is not set.[/]")
        sys.exit(1)
    try:
        from .store.db import get_engine, init_db
    except ImportError:
        console.print("[bold red]✗ The [db] extra isn't installed: pip install -e \".[db]\"[/]")
        sys.exit(1)
    engine = get_engine(url)
    init_db(engine)
    return engine


@db.command("init")
def db_init() -> None:
    """Create the tables and views (idempotent)."""
    _store_engine()
    console.print("[bold green]✓ Database ready[/]")


@db.command("create-project")
@click.argument("slug")
@click.option("--repo-url", default=None)
def db_create_project(slug: str, repo_url: str | None) -> None:
    """Create project SLUG (no-op if it exists)."""
    from .store.repository import create_project

    create_project(_store_engine(), slug, repo_url)
    console.print(f"[bold green]✓ Project[/] {slug}")


@db.command("create-token")
@click.argument("slug")
@click.option("--label", default=None, help="A name for this token, e.g. github-actions.")
def db_create_token(slug: str, label: str | None) -> None:
    """Create an API token for project SLUG. Prints it once; only its hash is stored."""
    from .store.repository import ProjectNotFound, create_token

    try:
        token = create_token(_store_engine(), slug, label)
    except ProjectNotFound:
        console.print(f"[bold red]✗ No project {slug!r}; create it first with `repoguard db create-project`.[/]")
        sys.exit(1)
    click.echo(token)


@db.command("revoke-tokens")
@click.argument("slug")
@click.option("--label", default=None, help="Only revoke tokens with this label.")
def db_revoke_tokens(slug: str, label: str | None) -> None:
    """Revoke project SLUG's tokens."""
    from .store.repository import ProjectNotFound, revoke_tokens

    try:
        count = revoke_tokens(_store_engine(), slug, label)
    except ProjectNotFound:
        console.print(f"[bold red]✗ No project {slug!r}.[/]")
        sys.exit(1)
    console.print(f"Revoked {count} token(s)")


@main.command()
def mcp() -> None:
    """Start the RepoGuard MCP server (stdio transport)."""
    from .mcp_server import mcp_app

    mcp_app.run()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PUSH_TIMEOUT = 60


def _push_record(url: str, token: str, record: dict) -> None:
    """POST the run record to a repoguard server; exits 1 on failure."""
    import httpx

    endpoint = url.rstrip("/") + "/api/runs"
    try:
        res = httpx.post(endpoint, json=record, headers={"Authorization": f"Bearer {token}"}, timeout=_PUSH_TIMEOUT)
    except httpx.HTTPError as exc:
        console.print(f"[bold red]✗ Push to {endpoint} failed:[/] {exc}")
        sys.exit(1)
    if res.status_code not in (200, 201):
        console.print(f"[bold red]✗ Push rejected ({res.status_code}):[/] {res.text[:500]}")
        sys.exit(1)
    click.echo(f"Pushed run {res.json().get('run_id')} to {url}", err=True)


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
        table.add_row("Mutation score", f"{m.score:.2f}%  ({m.killed}/{m.total} killed)")

    console.print(table)

    if result.risk:
        risk_table = Table(title="Top Risk Files")
        risk_table.add_column("File")
        risk_table.add_column("Risk Score")
        for r in result.risk[:5]:
            risk_color = "red" if r.score > 0.5 else "yellow" if r.score > 0.2 else "green"
            risk_table.add_row(r.file, f"[{risk_color}]{r.score:.3f}[/]")
        console.print(risk_table)


if __name__ == "__main__":  # `python -m repoguard_engine.cli`, pinned to this interpreter
    main()
