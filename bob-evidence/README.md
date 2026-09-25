# bob-evidence

Evidence collected during Bob-driven RepoGuard runs.

Each run creates a subdirectory named by date and target repo:

```
bob-evidence/
└── 2025-01-15_demo-repo/
    ├── before-coverage.json
    ├── after-coverage.json
    ├── gap-report.json
    ├── mutation-report.json
    ├── screenshot-before.png
    ├── screenshot-after.png
    └── summary.md
```

This folder is included in `.gitignore` for large binary files (PNG, MP4).
Text reports (JSON, MD) are tracked.
