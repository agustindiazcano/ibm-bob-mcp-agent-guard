# RepoGuard

> AI-powered test quality guard for any Python repository.

RepoGuard measures test coverage, finds gaps, hunts mutations, and drives Bob to fix everything — all from a single CLI command or MCP server.

## Quick Start

```bash
pip install -e .
repoguard analyze ./my-project
repoguard fix ./my-project
repoguard serve
```

## Commands

| Command | Description |
|---|---|
| `repoguard analyze` | Measure test coverage and quality gaps |
| `repoguard fix` | Bob-driven fix loop |
| `repoguard gate` | CI gate — fail if quality thresholds not met |
| `repoguard serve` | Start the web dashboard |
| `repoguard mcp` | Start the MCP server for Bob |

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for a full breakdown.

## Demo

See [docs/DEMO.md](docs/DEMO.md) for a walkthrough using the bundled `demo-repo/` fixture.

## Building with Bob

See [docs/BUILD_WITH_BOB.md](docs/BUILD_WITH_BOB.md) for how this project was built using Bob as the AI pair programmer.

# 🛡️ TestMind AI (ibm-bob-mcp-guard)
**The Full-Stack QA Agent Swarm orchestrated by IBM Bob & MCP**

[![IBM Bob IDE](https://img.shields.io/badge/Built%20for-IBM%20Bob%20IDE-0f62fe?style=for-the-badge)](https://ibm.com)
[![MCP Powered](https://img.shields.io/badge/Protocol-MCP%20Ready-4a4a4a?style=for-the-badge)](https://modelcontextprotocol.io/)
[![Python FastAPI](https://img.shields.io/badge/Engine-Python%20%7C%20FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)

TestMind AI goes beyond traditional static analysis. It transforms **IBM Bob** from a coding assistant into a fully autonomous QA department by leveraging a **Multi-Agent Swarm architecture**. 

Instead of relying on a single LLM prompt, it uses Bob's custom modes to orchestrate a team of specialized AI agents working in parallel. Empowered by a custom **MCP (Model Context Protocol)** server, the swarm can physically interact with your project to:

- 🔬 **Hunt Code Mutations:** Generate and execute unit tests, ensuring asserts actually catch bugs (not just vanity coverage).
- 🌐 **Fuzz APIs:** Autonomously test FastAPI/REST endpoints for unhandled exceptions.
- 👁️ **Explore UIs:** Spin up Playwright browsers, navigate web apps, and perform pixel-perfect visual regression testing.

Available right inside your IDE, from the CLI, or via a real-time Web Dashboard.
