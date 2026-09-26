"""Core measurement functions: coverage, gaps, mutation, risk, dashboard."""

from __future__ import annotations

import ast
import copy
import dataclasses
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CoverageResult:
    percent: float
    covered_lines: int
    total_lines: int
    missing_lines: dict[str, list[int]] = field(default_factory=dict)


@dataclass
class GapReport:
    uncovered_functions: list[str] = field(default_factory=list)
    uncovered_files: list[str] = field(default_factory=list)
    missing_lines_by_file: dict[str, list[int]] = field(default_factory=dict)


@dataclass
class MutationResult:
    score: float
    killed: int
    survived: int
    total: int
    surviving_mutant_ids: list[int] = field(default_factory=list)


@dataclass
class RiskScore:
    file: str
    score: float  # 0.0 – 1.0
    reasons: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# repoguard-out helpers
# ---------------------------------------------------------------------------

def _write_out(repo_path: Path, name: str, data: object) -> None:
    """Write *data* as JSON to <repo_path>/repoguard-out/<name>.json."""
    out_dir = repo_path / "repoguard-out"
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"{name}.json").write_text(
        json.dumps(data, indent=2, default=str), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------

def measure_coverage(repo_path: str | Path) -> CoverageResult:
    """Run pytest with coverage on *repo_path*, write repoguard-out/coverage.json, return CoverageResult."""
    repo = Path(repo_path)
    # Per-run data/report paths: concurrent measurements of the same repo
    # (e.g. /api/analyze + /api/stream) would otherwise erase each other's
    # .coverage and read a half-written coverage.json.
    with tempfile.TemporaryDirectory(prefix="repoguard-cov-") as tmp:
        coverage_json = Path(tmp) / "coverage.json"
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--cov", f"--cov-report=json:{coverage_json}", "-q", "--tb=no"],
            cwd=repo,
            env={**os.environ, "COVERAGE_FILE": str(Path(tmp) / ".coverage")},
            capture_output=True,
            text=True,
            timeout=120,
        )
        if not coverage_json.exists():
            # A missing coverage.json means pytest/pytest-cov failed to run, not
            # that the repo has 0% coverage — report the failure instead of a
            # fabricated zero (AGENTS.md: never claim a result you did not measure).
            raise RuntimeError(
                f"pytest did not produce coverage.json (exit code {proc.returncode}).\n"
                f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
            )
        data = json.loads(coverage_json.read_text(encoding="utf-8"))

    totals = data.get("totals", {})
    missing: dict[str, list[int]] = {}
    for fname, fdata in data.get("files", {}).items():
        if fdata.get("missing_lines"):
            missing[fname] = fdata["missing_lines"]

    result = CoverageResult(
        percent=totals.get("percent_covered", 0.0),
        covered_lines=totals.get("covered_lines", 0),
        total_lines=totals.get("num_statements", 0),
        missing_lines=missing,
    )
    _write_out(repo, "coverage", dataclasses.asdict(result))
    return result


def find_coverage_gaps(coverage: CoverageResult, repo_path: str | Path | None = None) -> GapReport:
    """Derive a structured gap report from a CoverageResult, write repoguard-out/gaps.json if repo_path given."""
    gap = GapReport()
    gap.missing_lines_by_file = dict(coverage.missing_lines)
    gap.uncovered_files = [f for f, lines in coverage.missing_lines.items() if lines]
    if repo_path is not None:
        _write_out(Path(repo_path), "gaps", dataclasses.asdict(gap))
    return gap


# ---------------------------------------------------------------------------
# AST mutation engine
# ---------------------------------------------------------------------------

@dataclass
class _Mutant:
    index: int
    description: str
    file_rel: str          # path relative to repo root
    mutated_source: str


# --- operator transformers ---

_CMP_MAP: dict[type, type] = {
    ast.Eq:    ast.NotEq,
    ast.NotEq: ast.Eq,
    ast.Lt:    ast.GtE,
    ast.GtE:   ast.Lt,
    ast.Gt:    ast.LtE,
    ast.LtE:   ast.Gt,
}

_BIN_MAP: dict[type, type] = {
    ast.Add:  ast.Sub,
    ast.Sub:  ast.Add,
    ast.Mult: ast.Div,
    ast.Div:  ast.Mult,
}

_BOOL_MAP: dict[type, type] = {
    ast.And: ast.Or,
    ast.Or:  ast.And,
}


class _ComparisonTransformer(ast.NodeTransformer):
    """Flip one comparison operator per instance."""

    def __init__(self, target_index: int) -> None:
        self._target = target_index
        self._counter = 0
        self.description = ""

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        new_ops = []
        for op in node.ops:
            if type(op) in _CMP_MAP and self._counter == self._target:
                new_op = _CMP_MAP[type(op)]()
                self.description = f"comparison {type(op).__name__} → {type(new_op).__name__}"
                new_ops.append(new_op)
                self._counter += 1
            else:
                if type(op) in _CMP_MAP:
                    self._counter += 1
                new_ops.append(op)
        node.ops = new_ops
        return self.generic_visit(node)


class _ArithmeticTransformer(ast.NodeTransformer):
    """Flip one arithmetic operator per instance."""

    def __init__(self, target_index: int) -> None:
        self._target = target_index
        self._counter = 0
        self.description = ""

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        if type(node.op) in _BIN_MAP and self._counter == self._target:
            new_op = _BIN_MAP[type(node.op)]()
            self.description = f"arithmetic {type(node.op).__name__} → {type(new_op).__name__}"
            node.op = new_op
            self._counter += 1
        elif type(node.op) in _BIN_MAP:
            self._counter += 1
        return self.generic_visit(node)


class _BooleanTransformer(ast.NodeTransformer):
    """Flip one boolean operator per instance."""

    def __init__(self, target_index: int) -> None:
        self._target = target_index
        self._counter = 0
        self.description = ""

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        if type(node.op) in _BOOL_MAP and self._counter == self._target:
            new_op = _BOOL_MAP[type(node.op)]()
            self.description = f"boolean {type(node.op).__name__} → {type(new_op).__name__}"
            node.op = new_op
            self._counter += 1
        elif type(node.op) in _BOOL_MAP:
            self._counter += 1
        return self.generic_visit(node)


class _ConstantTransformer(ast.NodeTransformer):
    """Flip one constant per instance: True↔False, int n → n+1."""

    def __init__(self, target_index: int) -> None:
        self._target = target_index
        self._counter = 0
        self.description = ""

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if isinstance(node.value, bool):
            if self._counter == self._target:
                new_val = not node.value
                self.description = f"constant {node.value} → {new_val}"
                self._counter += 1
                return ast.Constant(value=new_val)
            self._counter += 1
        elif isinstance(node.value, int):
            if self._counter == self._target:
                new_val = node.value + 1
                self.description = f"constant {node.value} → {new_val}"
                self._counter += 1
                return ast.Constant(value=new_val)
            self._counter += 1
        return node


class _ReturnNoneTransformer(ast.NodeTransformer):
    """Replace one non-None return expression with None."""

    def __init__(self, target_index: int) -> None:
        self._target = target_index
        self._counter = 0
        self.description = ""

    def visit_Return(self, node: ast.Return) -> ast.AST:
        if node.value is not None and not (
            isinstance(node.value, ast.Constant) and node.value.value is None
        ):
            if self._counter == self._target:
                self.description = "return <expr> → return None"
                self._counter += 1
                return ast.Return(value=ast.Constant(value=None))
            self._counter += 1
        return node


class _RemoveRaiseTransformer(ast.NodeTransformer):
    """Replace one raise statement with pass."""

    def __init__(self, target_index: int) -> None:
        self._target = target_index
        self._counter = 0
        self.description = ""

    def visit_Raise(self, node: ast.Raise) -> ast.AST:
        if self._counter == self._target:
            self.description = "raise → pass"
            self._counter += 1
            return ast.Pass()
        self._counter += 1
        return node


def _count_targets(tree: ast.AST, transformer_cls: type) -> int:
    """Count how many mutation sites exist for a given transformer class."""
    counter_obj = transformer_cls(target_index=-1)  # -1 → never mutates, just counts
    counter_obj._target = -1  # ensure no mutation fires

    class _Counter(ast.NodeVisitor):
        def __init__(self) -> None:
            self.n = 0

    visitor_map = {
        _ComparisonTransformer: ("visit_Compare", ast.Compare, "_CMP_MAP"),
        _ArithmeticTransformer: ("visit_BinOp", ast.BinOp, "_BIN_MAP"),
        _BooleanTransformer:    ("visit_BoolOp", ast.BoolOp, "_BOOL_MAP"),
        _ConstantTransformer:   ("visit_Constant", ast.Constant, None),
        _ReturnNoneTransformer: ("visit_Return", ast.Return, None),
        _RemoveRaiseTransformer: ("visit_Raise", ast.Raise, None),
    }

    method_name = visitor_map[transformer_cls][0]
    node_type = visitor_map[transformer_cls][1]

    count = 0
    for node in ast.walk(tree):
        if transformer_cls is _ComparisonTransformer and isinstance(node, ast.Compare):
            count += sum(1 for op in node.ops if type(op) in _CMP_MAP)
        elif transformer_cls is _ArithmeticTransformer and isinstance(node, ast.BinOp):
            if type(node.op) in _BIN_MAP:
                count += 1
        elif transformer_cls is _BooleanTransformer and isinstance(node, ast.BoolOp):
            if type(node.op) in _BOOL_MAP:
                count += 1
        elif transformer_cls is _ConstantTransformer and isinstance(node, ast.Constant):
            if isinstance(node.value, (bool, int)) and not isinstance(node.value, type(None)):
                count += 1
        elif transformer_cls is _ReturnNoneTransformer and isinstance(node, ast.Return):
            if node.value is not None and not (
                isinstance(node.value, ast.Constant) and node.value.value is None
            ):
                count += 1
        elif transformer_cls is _RemoveRaiseTransformer and isinstance(node, ast.Raise):
            count += 1
    return count


_TRANSFORMER_CLASSES = [
    _ComparisonTransformer,
    _ArithmeticTransformer,
    _BooleanTransformer,
    _ConstantTransformer,
    _ReturnNoneTransformer,
    _RemoveRaiseTransformer,
]


def _generate_mutants(source_path: Path, file_rel: str, index_offset: int) -> list[_Mutant]:
    """Parse *source_path* and return one _Mutant per mutation site."""
    try:
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return []

    mutants: list[_Mutant] = []
    idx = index_offset

    for transformer_cls in _TRANSFORMER_CLASSES:
        n = _count_targets(tree, transformer_cls)
        for site in range(n):
            mutated_tree = transformer_cls(target_index=site).visit(copy.deepcopy(tree))
            transformer_obj = transformer_cls(target_index=site)
            transformer_obj.visit(copy.deepcopy(tree))
            description = transformer_obj.description or f"{transformer_cls.__name__} site {site}"
            try:
                ast.fix_missing_locations(mutated_tree)
                mutated_source = ast.unparse(mutated_tree)
            except Exception:
                continue
            mutants.append(_Mutant(
                index=idx,
                description=f"{file_rel}: {description}",
                file_rel=file_rel,
                mutated_source=mutated_source,
            ))
            idx += 1

    return mutants


def _run_mutant(
    repo_path: Path,
    mutant: _Mutant,
    tests_dir: str,
) -> bool:
    """
    Copy repo to a tempdir, apply mutant, run pytest.
    Returns True if the mutant was killed (tests caught it), False if it survived.
    Always cleans up the tempdir.
    """
    tmp = tempfile.mkdtemp(prefix="repoguard_mutant_")
    try:
        shutil.copytree(str(repo_path), tmp, dirs_exist_ok=True)
        target = Path(tmp) / mutant.file_rel
        target.write_text(mutant.mutated_source, encoding="utf-8")

        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--tb=no", "--no-header", tests_dir],
            cwd=tmp,
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )
        # Killed = tests failed (non-zero exit) or errors detected
        return proc.returncode != 0
    except Exception:
        # On error, treat as killed to avoid false survivors
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_mutation(
    repo_path: str | Path,
    paths_to_mutate: str = ".",
    tests_dir: str = "tests",
) -> MutationResult:
    """
    Run own AST mutation engine on *repo_path*.
    Writes repoguard-out/mutation.json. Returns MutationResult.
    """
    repo = Path(repo_path).resolve()
    mutate_root = (repo / paths_to_mutate).resolve()

    # Collect all .py files under paths_to_mutate, excluding tests and hidden dirs
    py_files: list[Path] = sorted(
        p for p in mutate_root.rglob("*.py")
        if not any(part.startswith(".") or part == "__pycache__" or part == tests_dir
                   for part in p.relative_to(repo).parts)
    )

    # Generate mutants
    all_mutants: list[_Mutant] = []
    for py_file in py_files:
        file_rel = str(py_file.relative_to(repo))
        mutants = _generate_mutants(py_file, file_rel, index_offset=len(all_mutants))
        all_mutants.extend(mutants)

    killed = 0
    survived = 0
    surviving_ids: list[int] = []

    for mutant in all_mutants:
        if _run_mutant(repo, mutant, tests_dir):
            killed += 1
        else:
            survived += 1
            surviving_ids.append(mutant.index)

    total = killed + survived
    score = round((killed / total * 100), 2) if total else 0.0

    result = MutationResult(
        score=score,
        killed=killed,
        survived=survived,
        total=total,
        surviving_mutant_ids=surviving_ids,
    )
    _write_out(repo, "mutation", dataclasses.asdict(result))
    return result


# ---------------------------------------------------------------------------
# Risk
# ---------------------------------------------------------------------------

def compute_risk(repo_path: str | Path, coverage: CoverageResult) -> list[RiskScore]:
    """Assign a risk score to each file based on coverage gaps and file size. Writes repoguard-out/risk.json."""
    repo = Path(repo_path)
    scores: list[RiskScore] = []
    for fname, missing in coverage.missing_lines.items():
        path = repo / fname
        try:
            total_lines = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        except OSError:
            total_lines = 1

        coverage_gap = len(missing) / max(total_lines, 1)
        risk = RiskScore(
            file=fname,
            score=round(min(coverage_gap, 1.0), 3),
            reasons=[f"{len(missing)} uncovered lines out of ~{total_lines}"],
        )
        scores.append(risk)

    scores.sort(key=lambda r: r.score, reverse=True)
    _write_out(repo, "risk", [dataclasses.asdict(r) for r in scores])
    return scores


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def build_dashboard_data(
    coverage: CoverageResult,
    gap: GapReport,
    mutation: MutationResult | None = None,
    risk: list[RiskScore] | None = None,
) -> dict:
    """Assemble a JSON-serialisable dict for the web dashboard."""
    return {
        "coverage": {
            "percent": coverage.percent,
            "covered_lines": coverage.covered_lines,
            "total_lines": coverage.total_lines,
        },
        "gaps": {
            "uncovered_files": gap.uncovered_files,
            "missing_lines_by_file": gap.missing_lines_by_file,
        },
        "mutation": (
            {
                "score": mutation.score,
                "killed": mutation.killed,
                "survived": mutation.survived,
                "total": mutation.total,
            }
            if mutation
            else None
        ),
        "risk": (
            [{"file": r.file, "score": r.score, "reasons": r.reasons} for r in risk]
            if risk
            else []
        ),
    }
