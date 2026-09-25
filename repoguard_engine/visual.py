"""Visual testing utilities: screenshots, pixel diff, console logs, accessibility."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ScreenshotResult:
    path: str
    width: int
    height: int
    ok: bool
    error: str = ""


@dataclass
class PixelDiffResult:
    different_pixels: int
    total_pixels: int
    diff_percent: float
    diff_image_path: str = ""


@dataclass
class ConsoleLogEntry:
    level: str  # "log", "warn", "error"
    message: str


@dataclass
class A11yResult:
    violations: list[dict] = field(default_factory=list)
    passes: int = 0
    incomplete: int = 0


def capture_screenshot(
    url: str,
    output_path: str | Path,
    viewport: tuple[int, int] = (1280, 720),
) -> ScreenshotResult:
    """
    Capture a screenshot of *url* using Playwright (if available).
    Falls back gracefully when Playwright is not installed.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright  # type: ignore

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
            page.goto(url)
            page.screenshot(path=str(output))
            browser.close()

        return ScreenshotResult(
            path=str(output),
            width=viewport[0],
            height=viewport[1],
            ok=True,
        )
    except ImportError:
        return ScreenshotResult(
            path="",
            width=0,
            height=0,
            ok=False,
            error="playwright not installed — run: pip install playwright && playwright install",
        )
    except Exception as exc:
        return ScreenshotResult(path="", width=0, height=0, ok=False, error=str(exc))


def pixel_diff(
    baseline_path: str | Path,
    current_path: str | Path,
    output_path: str | Path | None = None,
) -> PixelDiffResult:
    """Compare two screenshots pixel-by-pixel. Requires Pillow."""
    try:
        from PIL import Image, ImageChops  # type: ignore
        import numpy as np  # type: ignore

        baseline = Image.open(baseline_path).convert("RGB")
        current = Image.open(current_path).convert("RGB")

        if baseline.size != current.size:
            current = current.resize(baseline.size, Image.LANCZOS)

        diff = ImageChops.difference(baseline, current)
        arr = np.array(diff)
        different = int(np.any(arr > 0, axis=2).sum())
        total = baseline.width * baseline.height

        diff_path = ""
        if output_path:
            diff.save(str(output_path))
            diff_path = str(output_path)

        return PixelDiffResult(
            different_pixels=different,
            total_pixels=total,
            diff_percent=round(different / max(total, 1) * 100, 2),
            diff_image_path=diff_path,
        )
    except ImportError:
        return PixelDiffResult(
            different_pixels=-1,
            total_pixels=-1,
            diff_percent=-1.0,
        )


def collect_console_logs(url: str) -> list[ConsoleLogEntry]:
    """Collect browser console messages from *url* using Playwright."""
    try:
        from playwright.sync_api import sync_playwright  # type: ignore

        logs: list[ConsoleLogEntry] = []

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.on("console", lambda msg: logs.append(ConsoleLogEntry(level=msg.type, message=msg.text)))
            page.goto(url)
            page.wait_for_load_state("networkidle")
            browser.close()

        return logs
    except ImportError:
        return []


def check_accessibility(url: str) -> A11yResult:
    """Run axe-core accessibility checks on *url* using Playwright + axe-playwright."""
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        from axe_playwright_python.sync_playwright import Axe  # type: ignore

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            axe = Axe()
            results = axe.run(page)
            browser.close()

        return A11yResult(
            violations=results.get("violations", []),
            passes=len(results.get("passes", [])),
            incomplete=len(results.get("incomplete", [])),
        )
    except ImportError:
        return A11yResult()
