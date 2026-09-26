"""phase17-api: read routes, POST /api/runs ingest with project tokens,
token-gated /api/analyze?persist=true, and a real `repoguard analyze
--push` against a real `repoguard serve` over loopback."""

import copy
import os
import shutil
import subprocess
import sys
import time
import uuid

import httpx
from fastapi.testclient import TestClient

from repoguard_engine.pipeline import run_pipeline
from repoguard_engine.store.db import get_engine, init_db
from repoguard_engine.store.repository import create_project, create_token, revoke_tokens, save_record
from repoguard_engine.web.server import app

from _util import free_port, sqlite_url, temp_demo_copy

repo = temp_demo_copy()
server = None
try:
    client = TestClient(app)
    os.environ.pop("REPOGUARD_DATABASE_URL", None)
    assert client.get("/api/projects").status_code == 503, "expected 503 with no database configured"
    assert client.get("/api/analyze", params={"repo_path": str(repo), "persist": "true"}).status_code == 503

    url = sqlite_url(repo.parent)
    os.environ["REPOGUARD_DATABASE_URL"] = url
    engine = get_engine(url)
    init_db(engine)
    result = run_pipeline(repo, project="demo", build_record=True, persist=False)
    save_record(engine, result.record)

    runs = client.get("/api/projects/demo/runs").json()
    assert len(runs) == 1 and runs[0]["coverage_pct"] == result.coverage.percent, runs
    trend = client.get("/api/projects/demo/trend").json()
    assert trend[0]["coverage_pct"] == result.coverage.percent and trend[0]["passed_gate"] == 0
    for route in ("operators", "risk-heatmap", "fix-effect", "survivors", "flaky"):
        assert client.get(f"/api/projects/demo/{route}").status_code == 200, route
    assert client.get("/api/projects/nope/trend").status_code == 404
    assert [p["slug"] for p in client.get("/api/projects").json()] == ["demo"]
    print("read routes: runs/trend match the stored run exactly; 503 without a DB, 404 for an unknown project")

    create_project(engine, "other")
    token = create_token(engine, "demo", "ci")
    other_token = create_token(engine, "other", "ci")
    body = copy.deepcopy(result.record)
    body["run_id"] = str(uuid.uuid4())
    auth = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/runs", json=body).status_code == 401
    assert client.post("/api/runs", json=body, headers={"Authorization": "Bearer nope"}).status_code == 401
    first = client.post("/api/runs", json=body, headers=auth)
    assert first.status_code == 201 and first.json()["run_id"] == body["run_id"], first.text
    again = client.post("/api/runs", json=body, headers=auth)
    assert again.status_code == 200 and again.json()["run_id"] == body["run_id"], "retry not idempotent"
    bad = copy.deepcopy(body)
    bad["run_id"] = str(uuid.uuid4())
    bad["coverage"]["covered_lines"] = bad["coverage"]["total_lines"] + 1
    assert client.post("/api/runs", json=bad, headers=auth).status_code == 422
    stolen = client.post("/api/runs", json=body, headers={"Authorization": f"Bearer {other_token}"})
    assert stolen.status_code == 409, "a token for project X wrote a run that belongs to project Y"
    revoke_tokens(engine, "demo", "ci")
    body["run_id"] = str(uuid.uuid4())
    assert client.post("/api/runs", json=body, headers=auth).status_code == 401, "revoked token accepted"
    stored = client.get("/api/projects/demo/runs").json()
    assert sum(r["source"] == "ci" for r in stored) == 1
    print("ingest: 401 no/wrong/revoked token, 201 then 200 on retry, 422 inconsistent counts, 409 cross-project")

    token = create_token(engine, "demo", "persist")
    params = {"repo_path": str(repo), "persist": "true"}
    assert client.get("/api/analyze", params=params).status_code == 401
    persisted = client.get("/api/analyze", params=params, headers={"Authorization": f"Bearer {token}"})
    assert persisted.status_code == 200 and persisted.json().get("run_id"), persisted.text
    plain = client.get("/api/analyze", params={"repo_path": str(repo)}).json()
    assert "run_id" not in plain, "persisted without persist=true"
    print("/api/analyze: persist=true needs a project token; default never writes, even with a database")

    # Real loopback: `repoguard serve` + `repoguard analyze --push`.
    push_db = repo.parent / "push"
    push_db.mkdir()
    env = {**os.environ, "REPOGUARD_DATABASE_URL": sqlite_url(push_db)}
    port = free_port()
    exe = [sys.executable, "-m", "repoguard_engine.cli"]
    subprocess.run([*exe, "db", "create-project", "pushed"], env=env, check=True, capture_output=True, timeout=60)
    push_token = subprocess.run(
        [*exe, "db", "create-token", "pushed", "--label", "loopback"], env=env, check=True, capture_output=True, text=True, timeout=60
    ).stdout.strip().splitlines()[-1]
    server = subprocess.Popen([*exe, "serve", "--port", str(port)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            if httpx.get(f"{base}/api/projects", timeout=1).status_code == 200:
                break
        except httpx.HTTPError:
            time.sleep(0.2)
    else:
        raise AssertionError("repoguard serve didn't come up")
    push_env = {k: v for k, v in env.items() if k != "REPOGUARD_DATABASE_URL"}
    push_env["REPOGUARD_TOKEN"] = push_token
    subprocess.run([*exe, "analyze", str(repo), "--push", base], env=push_env, check=True, capture_output=True, timeout=300)
    pushed = httpx.get(f"{base}/api/projects/pushed/runs", timeout=10).json()
    assert len(pushed) == 1 and pushed[0]["source"] == "ci", pushed
    assert round(pushed[0]["coverage_pct"], 1) == 65.1, pushed
    print(f"loopback: analyze --push -> repoguard serve stored 1 run ({pushed[0]['coverage_pct']:.1f}%), no local [db] use")
    print("OK")
finally:
    if server is not None:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
    os.environ.pop("REPOGUARD_DATABASE_URL", None)
    shutil.rmtree(repo.parent, ignore_errors=True)
