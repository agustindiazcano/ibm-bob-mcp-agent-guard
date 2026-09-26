"""AST mutation engine: inject one small bug at a time, rerun the suite,
count how many the tests catch.

Split out of core.py (which re-exports the public names) once per-mutant
records pushed it past the ~600-line limit (AGENTS.md Section 6).

Guarantees a score has to meet before it's reported:
- The unmutated suite passes in the repo itself (baseline guard).
- The unmutated suite also passes in an isolated copy made exactly the way
  mutant copies are made (sham-mutant control). A test that fails *because*
  it runs from a copy would otherwise make every mutant look killed.
- At least one mutant exists (NoMutantsError instead of a silent 0/0).
- Every subprocess runs with PYTHONDONTWRITEBYTECODE=1 and sys.executable
  (AGENTS.md Section 9).

Each mutant gets a stable fingerprint -- sha1(file, enclosing function,
operator description, ordinal within that function) -- so the same mutant
can be matched across runs, across file-scoped vs whole-repo runs, and
across the swarm's lanes, even when unrelated code elsewhere changes.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import Executor, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from ._common import COPY_IGNORE, require_repo_dir, write_out

# Bump whenever the mutation logic changes in a way the operator maps below
# don't capture. Changing operators is an AGENTS.md Section 8 ask-first item.
MUTATION_ENGINE_REVISION = 1

_MUTANT_TIMEOUT = 60
_BASELINE_TIMEOUT = 120

OUTCOMES = ("killed", "survived", "timeout", "error")


class NoMutantsError(ValueError):
    """paths_to_mutate produced zero mutants. Deliberately not a
    RuntimeError: a 0/0 run is a bad request, not a failed suite."""


class MutationEnvironmentError(RuntimeError):
    """The unmutated suite fails in an isolated copy, so every mutant would
    score "killed" for reasons that have nothing to do with the mutation."""


@dataclass
class MutantRecord:
    index: int
    fingerprint: str
    file: str
    function: str
    lineno: int
    operator: str
    description: str
    original_line: str
    outcome: str  # one of OUTCOMES; everything but "survived" counts as killed


@dataclass
class MutationResult:
    score: float
    killed: int
    survived: int
    total: int
    surviving_mutant_ids: list[int] = field(default_factory=list)
    # Per-mutant records. Kept out of repoguard-out/mutation.json (written
    # from the five fields above, unchanged) and written to mutants.json.
    mutants: list[MutantRecord] = field(default_factory=list)

    def outcome_counts(self) -> dict[str, int]:
        return {o: sum(1 for m in self.mutants if m.outcome == o) for o in OUTCOMES}


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

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


class _SiteTransformer(ast.NodeTransformer):
    """Base: mutate exactly one site (the target_index-th), recording what
    changed and on which line."""

    operator = ""

    def __init__(self, target_index: int) -> None:
        self._target = target_index
        self._counter = 0
        self.description = ""
        self.lineno = 0

    def _hit(self, node: ast.AST, description: str) -> None:
        self.description = description
        self.lineno = getattr(node, "lineno", 0)


class _ComparisonTransformer(_SiteTransformer):
    """Flip one comparison operator per instance."""

    operator = "comparison"

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        new_ops = []
        for op in node.ops:
            if type(op) in _CMP_MAP and self._counter == self._target:
                new_op = _CMP_MAP[type(op)]()
                self._hit(node, f"comparison {type(op).__name__} → {type(new_op).__name__}")
                new_ops.append(new_op)
                self._counter += 1
            else:
                if type(op) in _CMP_MAP:
                    self._counter += 1
                new_ops.append(op)
        node.ops = new_ops
        return self.generic_visit(node)


class _ArithmeticTransformer(_SiteTransformer):
    """Flip one arithmetic operator per instance."""

    operator = "arithmetic"

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        if type(node.op) in _BIN_MAP and self._counter == self._target:
            new_op = _BIN_MAP[type(node.op)]()
            self._hit(node, f"arithmetic {type(node.op).__name__} → {type(new_op).__name__}")
            node.op = new_op
            self._counter += 1
        elif type(node.op) in _BIN_MAP:
            self._counter += 1
        return self.generic_visit(node)


class _BooleanTransformer(_SiteTransformer):
    """Flip one boolean operator per instance."""

    operator = "boolean"

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        if type(node.op) in _BOOL_MAP and self._counter == self._target:
            new_op = _BOOL_MAP[type(node.op)]()
            self._hit(node, f"boolean {type(node.op).__name__} → {type(new_op).__name__}")
            node.op = new_op
            self._counter += 1
        elif type(node.op) in _BOOL_MAP:
            self._counter += 1
        return self.generic_visit(node)


class _ConstantTransformer(_SiteTransformer):
    """Flip one constant per instance: True↔False, int n → n+1."""

    operator = "constant"

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if isinstance(node.value, bool):
            if self._counter == self._target:
                new_val = not node.value
                self._hit(node, f"constant {node.value} → {new_val}")
                self._counter += 1
                return ast.copy_location(ast.Constant(value=new_val), node)
            self._counter += 1
        elif isinstance(node.value, int):
            if self._counter == self._target:
                new_val = node.value + 1
                self._hit(node, f"constant {node.value} → {new_val}")
                self._counter += 1
                return ast.copy_location(ast.Constant(value=new_val), node)
            self._counter += 1
        return node


class _ReturnNoneTransformer(_SiteTransformer):
    """Replace one non-None return expression with None."""

    operator = "return_none"

    def visit_Return(self, node: ast.Return) -> ast.AST:
        if node.value is not None and not (
            isinstance(node.value, ast.Constant) and node.value.value is None
        ):
            if self._counter == self._target:
                self._hit(node, "return <expr> → return None")
                self._counter += 1
                return ast.copy_location(ast.Return(value=ast.Constant(value=None)), node)
            self._counter += 1
        return node


class _RemoveRaiseTransformer(_SiteTransformer):
    """Replace one raise statement with pass."""

    operator = "remove_raise"

    def visit_Raise(self, node: ast.Raise) -> ast.AST:
        if self._counter == self._target:
            self._hit(node, "raise → pass")
            self._counter += 1
            return ast.copy_location(ast.Pass(), node)
        self._counter += 1
        return node


_TRANSFORMER_CLASSES = [
    _ComparisonTransformer,
    _ArithmeticTransformer,
    _BooleanTransformer,
    _ConstantTransformer,
    _ReturnNoneTransformer,
    _RemoveRaiseTransformer,
]


def _operators_hash() -> str:
    """sha256 of a canonical dump of the operator set. Two runs are only
    comparable (e.g. in stored history) when this matches."""
    canon = {
        "revision": MUTATION_ENGINE_REVISION,
        "transformers": [c.__name__ for c in _TRANSFORMER_CLASSES],
        "maps": {
            name: sorted(f"{a.__name__}->{b.__name__}" for a, b in mapping.items())
            for name, mapping in (("cmp", _CMP_MAP), ("bin", _BIN_MAP), ("bool", _BOOL_MAP))
        },
    }
    return hashlib.sha256(json.dumps(canon, sort_keys=True).encode()).hexdigest()


MUTATION_OPERATORS_HASH = _operators_hash()


def _count_targets(tree: ast.AST, transformer_cls: type) -> int:
    """Count how many mutation sites exist for a given transformer class."""
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
            if isinstance(node.value, (bool, int)):
                count += 1
        elif transformer_cls is _ReturnNoneTransformer and isinstance(node, ast.Return):
            if node.value is not None and not (
                isinstance(node.value, ast.Constant) and node.value.value is None
            ):
                count += 1
        elif transformer_cls is _RemoveRaiseTransformer and isinstance(node, ast.Raise):
            count += 1
    return count


# ---------------------------------------------------------------------------
# Mutant generation
# ---------------------------------------------------------------------------

@dataclass
class _Mutant:
    index: int
    file_rel: str          # posix path relative to repo root
    function: str
    lineno: int
    operator: str
    description: str
    ordinal: int
    original_line: str
    mutated_source: str

    @property
    def fingerprint(self) -> str:
        key = "\x1f".join((self.file_rel, self.function, self.description, str(self.ordinal)))
        return hashlib.sha1(key.encode("utf-8")).hexdigest()


def _function_spans(tree: ast.AST) -> list[tuple[int, int, str]]:
    """(start, end, qualname) for every function, qualname including
    enclosing classes/functions (e.g. "Cart.add")."""
    spans: list[tuple[int, int, str]] = []

    def walk(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qualname = f"{prefix}.{child.name}" if prefix else child.name
                if not isinstance(child, ast.ClassDef):
                    spans.append((child.lineno, child.end_lineno or child.lineno, qualname))
                walk(child, qualname)
            else:
                walk(child, prefix)

    walk(tree, "")
    return spans


def _function_at(spans: list[tuple[int, int, str]], lineno: int) -> str:
    """Innermost function containing lineno, or "<module>"."""
    containing = [s for s in spans if s[0] <= lineno <= s[1]]
    if not containing:
        return "<module>"
    return max(containing, key=lambda s: s[0])[2]


def _generate_mutants(source_path: Path, file_rel: str, index_offset: int) -> list[_Mutant]:
    """Parse *source_path* and return one _Mutant per mutation site."""
    try:
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return []

    lines = source.splitlines()
    spans = _function_spans(tree)
    seen: dict[tuple[str, str], int] = {}
    mutants: list[_Mutant] = []
    idx = index_offset

    for transformer_cls in _TRANSFORMER_CLASSES:
        for site in range(_count_targets(tree, transformer_cls)):
            transformer = transformer_cls(target_index=site)
            mutated_tree = transformer.visit(copy.deepcopy(tree))
            try:
                ast.fix_missing_locations(mutated_tree)
                mutated_source = ast.unparse(mutated_tree)
            except Exception:
                continue
            description = transformer.description or f"{transformer_cls.__name__} site {site}"
            function = _function_at(spans, transformer.lineno)
            ordinal = seen.get((function, description), 0)
            seen[(function, description)] = ordinal + 1
            original = lines[transformer.lineno - 1].strip() if 0 < transformer.lineno <= len(lines) else ""
            mutants.append(_Mutant(
                index=idx,
                file_rel=file_rel,
                function=function,
                lineno=transformer.lineno,
                operator=transformer_cls.operator,
                description=description,
                ordinal=ordinal,
                original_line=original,
                mutated_source=mutated_source,
            ))
            idx += 1

    return mutants


def _files_to_mutate(repo: Path, mutate_root: Path, tests_dir: str) -> list[Path]:
    """Source files in scope: mutate_root itself if it's a file, else every
    .py under it minus tests, hidden dirs, caches and this tool's outputs."""
    excluded = {"__pycache__", tests_dir, "repoguard-out", "watson-evidence"}

    def in_scope(p: Path) -> bool:
        return not any(part.startswith(".") or part in excluded for part in p.relative_to(repo).parts)

    if mutate_root.is_file():
        if mutate_root.suffix != ".py" or not in_scope(mutate_root):
            raise NoMutantsError(f"paths_to_mutate must be a .py source file outside {tests_dir}/: {mutate_root}")
        return [mutate_root]
    if not mutate_root.is_dir():
        raise NoMutantsError(f"paths_to_mutate does not exist: {mutate_root}")
    return sorted(p for p in mutate_root.rglob("*.py") if in_scope(p))


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------

def _pytest_env() -> dict[str, str]:
    return {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


def _run_copy(repo_path: Path, tests_dir: str, mutant: _Mutant | None = None) -> str:
    """
    Copy the repo to a tempdir, apply *mutant* (None = apply nothing, the
    sham control), run pytest. Returns the outcome: "killed" (suite failed),
    "survived" (suite passed), "timeout" or "error" (couldn't run). Always
    removes the tempdir.
    """
    tmp = tempfile.mkdtemp(prefix="repoguard_mutant_")
    try:
        shutil.copytree(str(repo_path), tmp, dirs_exist_ok=True, ignore=COPY_IGNORE)
        if mutant is not None:
            (Path(tmp) / mutant.file_rel).write_text(mutant.mutated_source, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--tb=no", "--no-header", "-p", "no:cacheprovider", tests_dir],
            cwd=tmp,
            capture_output=True,
            text=True,
            env=_pytest_env(),
            timeout=_MUTANT_TIMEOUT,
        )
        return "survived" if proc.returncode == 0 else "killed"
    except subprocess.TimeoutExpired:
        return "timeout"
    except Exception:
        return "error"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _check_baseline(repo: Path, tests_dir: str) -> None:
    """A mutation score only means anything relative to a passing suite:
    _run_copy scores "killed" whenever pytest exits non-zero, so a red
    baseline would make every mutant look killed (AGENTS.md Section 4)."""
    baseline = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=no", "--no-header", "-p", "no:cacheprovider", tests_dir],
        cwd=repo,
        capture_output=True,
        text=True,
        env=_pytest_env(),
        timeout=_BASELINE_TIMEOUT,
    )
    if baseline.returncode != 0:
        raise RuntimeError(
            "Mutation testing requires a passing baseline test suite, but "
            f"pytest failed on the unmutated code (exit code {baseline.returncode}).\n"
            "Every mutant would trivially score \"killed\" against an already-"
            "failing suite, so no mutation score can be reported until this "
            "is fixed.\n"
            f"stdout:\n{baseline.stdout}\nstderr:\n{baseline.stderr}"
        )
    sham = _run_copy(repo, tests_dir)
    if sham != "survived":
        raise MutationEnvironmentError(
            f"The unmutated suite passes in {repo} but not in an isolated copy (sham mutant: {sham}). "
            "Something in the tests depends on where they run from (an absolute path, a file the copy "
            "skips, an editable install importing the original source), so every mutant would score "
            "\"killed\" regardless of the mutation. No mutation score is reported until that's fixed."
        )


def run_mutation(
    repo_path: str | Path,
    paths_to_mutate: str = ".",
    tests_dir: str = "tests",
    *,
    workers: int = 1,
    executor: Executor | None = None,
) -> MutationResult:
    """
    Run the AST mutation engine on *repo_path*.

    paths_to_mutate: a directory or a single .py file, relative to the repo.
    workers: mutants run in parallel on this many threads (each in its own
    copy and pytest process); results are identical to workers=1 because
    they're collected in generation order. executor: an existing pool to
    use instead (the swarm shares one across lanes).

    Writes repoguard-out/mutation.json (score/killed/survived/total/
    surviving_mutant_ids, unchanged format) and repoguard-out/mutants.json
    (one record per mutant with fingerprint and outcome). Returns
    MutationResult. Raises NoMutantsError for an empty scope, RuntimeError
    for a failing baseline, MutationEnvironmentError when the suite only
    fails in a copy.
    """
    if workers < 1:
        raise ValueError(f"workers must be >= 1, got {workers}")
    repo = require_repo_dir(repo_path).resolve()
    mutate_root = (repo / paths_to_mutate).resolve()

    all_mutants: list[_Mutant] = []
    for py_file in _files_to_mutate(repo, mutate_root, tests_dir):
        file_rel = py_file.relative_to(repo).as_posix()
        all_mutants.extend(_generate_mutants(py_file, file_rel, index_offset=len(all_mutants)))
    if not all_mutants:
        raise NoMutantsError(f"No mutants generated under {paths_to_mutate!r} in {repo}.")

    _check_baseline(repo, tests_dir)

    def run_one(mutant: _Mutant) -> str:
        return _run_copy(repo, tests_dir, mutant)

    if executor is not None:
        outcomes = list(executor.map(run_one, all_mutants))
    elif workers > 1:
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="repoguard-mutant") as pool:
            outcomes = list(pool.map(run_one, all_mutants))
    else:
        outcomes = [run_one(m) for m in all_mutants]

    records = [
        MutantRecord(
            index=m.index,
            fingerprint=m.fingerprint,
            file=m.file_rel,
            function=m.function,
            lineno=m.lineno,
            operator=m.operator,
            description=m.description,
            original_line=m.original_line,
            outcome=outcome,
        )
        for m, outcome in zip(all_mutants, outcomes)
    ]
    surviving_ids = [r.index for r in records if r.outcome == "survived"]
    total = len(records)
    survived = len(surviving_ids)
    killed = total - survived

    result = MutationResult(
        score=round(killed / total * 100, 2),
        killed=killed,
        survived=survived,
        total=total,
        surviving_mutant_ids=surviving_ids,
        mutants=records,
    )
    summary = {k: v for k, v in dataclasses.asdict(result).items() if k != "mutants"}
    write_out(repo, "mutation", summary)
    write_out(
        repo,
        "mutants",
        {
            "engine_revision": MUTATION_ENGINE_REVISION,
            "operators_hash": MUTATION_OPERATORS_HASH,
            "counts": result.outcome_counts(),
            "mutants": [dataclasses.asdict(r) for r in records],
        },
    )
    return result
