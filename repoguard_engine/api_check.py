"""Detect untested FastAPI endpoints and optionally run smoke tests."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class EndpointInfo:
    file: str
    function: str
    method: str
    path: str
    has_test: bool = False


def find_untested_endpoints(repo_path: str | Path) -> list[EndpointInfo]:
    """
    Walk *repo_path* for FastAPI route decorators and cross-reference against
    the test files to determine which endpoints have no test coverage.
    """
    repo = Path(repo_path)
    endpoints: list[EndpointInfo] = []

    # Collect all route-decorated functions in source files
    for py_file in repo.rglob("*.py"):
        if "test_" in py_file.name or py_file.parts[-1].startswith("test"):
            continue
        try:
            tree = ast.parse(py_file.read_text(), filename=str(py_file))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for decorator in node.decorator_list:
                method, route_path = _extract_route(decorator)
                if method:
                    endpoints.append(
                        EndpointInfo(
                            file=str(py_file.relative_to(repo)),
                            function=node.name,
                            method=method,
                            path=route_path or "/",
                        )
                    )

    # Mark endpoints that appear in test files
    test_bodies: list[str] = []
    for tf in repo.rglob("test_*.py"):
        try:
            test_bodies.append(tf.read_text())
        except OSError:
            pass
    combined = "\n".join(test_bodies)

    for ep in endpoints:
        if ep.function in combined or ep.path in combined:
            ep.has_test = True

    return endpoints


def _extract_route(decorator: ast.expr) -> tuple[str, str]:
    """Return (HTTP_METHOD, path) from a FastAPI route decorator node, or ('', '')."""
    http_methods = {"get", "post", "put", "patch", "delete", "head", "options"}
    if isinstance(decorator, ast.Call):
        func = decorator.func
        attr = getattr(func, "attr", None) or getattr(func, "id", None) or ""
        if attr.lower() in http_methods:
            path_arg = ""
            if decorator.args:
                arg = decorator.args[0]
                if isinstance(arg, ast.Constant):
                    path_arg = arg.value
            return attr.upper(), path_arg
    return "", ""


def run_endpoint_smoke_tests(
    base_url: str,
    endpoints: list[EndpointInfo],
) -> dict[str, dict]:
    """
    Fire a minimal HTTP request at each endpoint and return a status map.
    Requires the server to be running at *base_url*.
    """
    try:
        import httpx
    except ImportError:
        return {"error": "httpx not installed"}

    results: dict[str, dict] = {}
    with httpx.Client(base_url=base_url, timeout=5.0) as client:
        for ep in endpoints:
            key = f"{ep.method} {ep.path}"
            try:
                response = client.request(ep.method, ep.path)
                results[key] = {"status_code": response.status_code, "ok": response.is_success}
            except Exception as exc:
                results[key] = {"status_code": None, "ok": False, "error": str(exc)}

    return results
