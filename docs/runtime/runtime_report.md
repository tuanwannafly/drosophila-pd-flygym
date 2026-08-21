# Browser Runtime Report

Status: `PARTIAL_PASS_REAL_BROWSER`

The repository contains no real `viewer_pose.json` or imported rollout artifact.
Viewer-load and playback-with-pose checks require the external artifact path
supplied through `FLY_STUDIO_VIEWER_POSE` and were skipped in this repository
run. They were not replaced by synthetic data.

## Commands

```text
pip install -e ".[e2e]"
playwright install chromium
pytest -q tests/e2e
```

## Measurements

| Metric | Status | Value |
| --- | --- | --- |
| Initial load | PASS | 1197.97 ms wall time; DOMContentLoaded 929.40 ms; load 985.00 ms |
| Viewer initialization | NOT_MEASURED | Requires real pose artifact |
| Memory usage | OBSERVED | JS heap 10,000,000 / 13,400,000 bytes |
| Playback FPS | NOT_MEASURED | Requires real pose artifact |
| Timeline latency | NOT_MEASURED | Requires real pose artifact |

## E2E result

Command: `pytest -q -rs -p no:cacheprovider --run-e2e tests/e2e`

Result: `5 passed, 3 skipped`.

The passing checks covered app load, dataset tab, analysis tab, reports /
publication / plugins tabs, and invalid JSON handling. The skipped checks were
real pose loading, Timeline seek, and viewer playback because no real pose
artifact is present in the repository.

Screenshots from passing checks are stored in `docs/runtime/screenshots/`.

No scientific result or biological conclusion is produced by this runtime
validation layer.
