"""repoguard_engine — public API re-exports."""

from .core import (
    measure_coverage,
    find_coverage_gaps,
    run_mutation,
    compute_risk,
    build_dashboard_data,
)
from .api_check import find_untested_endpoints, run_endpoint_smoke_tests
from .visual import capture_screenshot, pixel_diff, collect_console_logs, check_accessibility
from .pipeline import run_pipeline

__all__ = [
    "measure_coverage",
    "find_coverage_gaps",
    "run_mutation",
    "compute_risk",
    "build_dashboard_data",
    "find_untested_endpoints",
    "run_endpoint_smoke_tests",
    "capture_screenshot",
    "pixel_diff",
    "collect_console_logs",
    "check_accessibility",
    "run_pipeline",
]
