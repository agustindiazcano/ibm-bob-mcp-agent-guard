"""CLI entry point: repoguard analyze | fix | gate | serve | mcp"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click
# Error text is escaped before printing: Rich would read an install hint
# like `pip install -e ".[db]"` as markup and silently drop the "[db]".
from rich.console import Console
from rich.markup import escape
from rich.table import Table

console = Console()
err_console = Console(stderr=True)


@click.group()
def main() -> None:
    """RepoGuard — AI-powered test quality guard."""


_project_option = click.option(
    "--project", default=None,
    help="Project slug to store the run under when REPOGUARD_DATABASE_URL is set "
         "(default: REPOGUARD_PROJECT, then GITHUB_REPOSITORY, then the repo directory name).",
)


def _run_pipeline_or_exit(repo_path: str, **kwargs):
    """run_pipeline, turning a storage failure into a clean exit 1 (no traceback)."""
    from .pipeline import run_pipeline
    from .store import StoreError

    try:
        return run_pipeline(repo_path, **kwargs)
    except StoreError as exc:
        err_console.print(f"[bold red]✗ Storage failed:[/] {escape(str(exc))}")
        sys.exit(1)


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
@_project_option
@click.option(
    "--push", "push_url", default=None,
    help="POST the measured run to a repoguard server's POST /api/runs "
         "(token from REPOGUARD_TOKEN, checked before measuring). Works "
         "without REPOGUARD_DATABASE_URL or the [db] extra.",
)
def analyze(
    repo_path: str, mutation: bool, endpoints: bool, json_output: bool, workers: int, summarize: bool,
    provider: str | None, project: str | None, push_url: str | None,
) -> None:
    """Measure test coverage and quality gaps in REPO_PATH.

    With REPOGUARD_DATABASE_URL set, the run is also stored (see
    docs/DATA_PLATFORM.md); nothing measured changes either way.
    """
    from .mutation import NoMutantsError

    push_token = os.environ.get("REPOGUARD_TOKEN", "").strip()
    if push_url and not push_token:
        console.print("[bold red]✗[/] --push requires REPOGUARD_TOKEN to be set.")
        sys.exit(1)

    # With --json-output, stdout carries only the JSON (pipeable into jq)
    (err_console if json_output else console).print(f"[bold cyan]Analysing[/] {repo_path} …")
    try:
        result = _run_pipeline_or_exit(
            repo_path,
            include_mutation=mutation,
            include_endpoints=endpoints,
            mutation_workers=workers,
            project=project,
        )
    except (NoMutantsError, RuntimeError) as exc:
        console.print(f"[bold red]✗ Mutation testing couldn't produce a score:[/] {exc}")
        sys.exit(1)

    if push_url:
        _push_run(push_url, push_token, result, project, endpoints)

    if json_output:
        # stdout stays the dashboard alone; the stored run id goes to stderr
        click.echo(json.dumps(result.dashboard, indent=2))
        if result.run_id:
            click.echo(f"Stored run {result.run_id} (project {result.project})", err=True)
        return

    _print_coverage_table(result)
    _print_stored(result)

    if summarize:
        from .narrative import generate_summary

        narrative = generate_summary(result.dashboard, provider=provider)
        if narrative.ok:
            console.print(f"\n[bold]AI summary ({narrative.provider} — advisory, not a measurement):[/]")
            console.print(narrative.text)
        else:
            console.print(f"\n[yellow]Summary unavailable:[/] {escape(narrative.error)}")


@main.command()
@click.argument("repo_path", default=".", type=click.Path(exists=True))
@click.option("--threshold", default=80.0, show_default=True, help="Coverage % gate threshold.")
@_project_option
def gate(repo_path: str, threshold: float, project: str | None) -> None:
    """CI gate: exit 1 if coverage is below THRESHOLD."""
    result = _run_pipeline_or_exit(repo_path, gate_threshold=threshold, project=project)
    _print_coverage_table(result)
    _print_stored(result)

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
    from .mutation import NoMutantsError
    from .watson_agent import run_fix_loop

    console.print(f"[bold cyan]Fix loop[/] {repo_path} …")
    try:
        result = run_fix_loop(repo_path, gate_threshold=threshold, publish=publish, provider=provider)
    except AIProviderError as exc:
        console.print(f"[bold red]✗ {escape(str(exc))}[/]")
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

    if result.status not in ("accepted", "partial"):
        console.print(f"[bold red]Fix loop failed with status: {result.status}[/]")
        sys.exit(1)
    console.print(f"[bold green]Fix loop completed with status: {result.status}[/]")


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


@main.group()
def db() -> None:
    """Manage the measurement-history database (REPOGUARD_DATABASE_URL)."""


def _ready_engine():
    """The store engine for a `db` subcommand, schema guaranteed to exist.
    Exits 1 (no traceback) if the URL is unset or the database can't be reached."""
    from .store import StoreError, database_url
    from .store.db import get_engine, init_db

    url = database_url()
    if url is None:
        err_console.print("[bold red]✗[/] REPOGUARD_DATABASE_URL is not set.")
        sys.exit(1)
    try:
        engine = get_engine(url)
        init_db(engine)
    except StoreError as exc:
        err_console.print(f"[bold red]✗[/] {escape(str(exc))}")
        sys.exit(1)
    return engine


@db.command("init")
def db_init() -> None:
    """Create tables and views if they don't exist yet."""
    _ready_engine()
    console.print("[bold green]✓[/] Database ready.")


@db.command("create-project")
@click.argument("slug")
def db_create_project(slug: str) -> None:
    """Create PROJECT_SLUG (idempotent)."""
    from .store import StoreError
    from .store.repository import create_project

    engine = _ready_engine()
    try:
        create_project(engine, slug)
    except StoreError as exc:
        err_console.print(f"[bold red]✗[/] {escape(str(exc))}")
        sys.exit(1)
    console.print(f"[bold green]✓[/] Project [bold]{slug}[/] ready.")


@db.command("create-token")
@click.argument("slug")
@click.option("--label", default=None, help="Optional label to identify this token later.")
def db_create_token(slug: str, label: str | None) -> None:
    """A new POST /api/runs ingest token for SLUG (must already exist).
    Printed once -- store it now, it is never shown again."""
    from .store import StoreError
    from .store.repository import create_token

    engine = _ready_engine()
    try:
        _, token = create_token(engine, slug, label=label)
    except StoreError as exc:
        err_console.print(f"[bold red]✗[/] {escape(str(exc))}")
        sys.exit(1)
    console.print(f"[bold green]✓[/] Token for [bold]{slug}[/] (shown once):")
    console.print(token)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _push_run(url: str, token: str, result, project: str | None, include_endpoints: bool) -> None:
    """POST the just-measured run to another repoguard server's /api/runs.
    Independent of REPOGUARD_DATABASE_URL / the [db] extra: builds the same
    schema-1 record ingest expects, using only store/context.py and
    store/record.py (no SQLAlchemy import)."""
    import httpx

    from .store.context import collect_context
    from .store.record import build_run_record, new_run_id

    ctx = collect_context(result.repo_path, project)
    record = build_run_record(
        ctx,
        run_id=new_run_id(),
        started_at=result.started_at,
        finished_at=result.finished_at,
        gate_threshold=result.gate_threshold,
        coverage=result.coverage,
        mutation=result.mutation,
        risk=result.risk,
        endpoints=result.endpoints if include_endpoints else None,
    )
    endpoint = url.rstrip("/") + "/api/runs"
    try:
        resp = httpx.post(endpoint, json=record, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    except httpx.HTTPError as exc:
        console.print(f"[bold red]✗ Push to {endpoint} failed:[/] {exc}")
        sys.exit(1)
    if resp.status_code not in (200, 201):
        console.print(f"[bold red]✗ Push to {endpoint} failed:[/] {resp.status_code} {resp.text}")
        sys.exit(1)
    body = resp.json()
    console.print(f"[bold green]✓ Pushed[/] run {body.get('run_id')} to {endpoint} (project {body.get('project')})")


def _print_stored(result) -> None:
    if result.run_id:
        console.print(f"Stored run {result.run_id} (project {result.project})")


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
