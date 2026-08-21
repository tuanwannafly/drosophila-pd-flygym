# REST API Preparation

The following endpoints are reserved for a future read/write service. This
document is a contract sketch only; no server implementation is included.

| Method | Path | Intended input/output |
| --- | --- | --- |
| GET | `/datasets` | List discovered, manifest-backed datasets |
| GET | `/dataset/{id}` | Return dataset metadata and integrity status |
| GET | `/rollout/{id}` | Return an imported rollout descriptor or pose reference |
| GET | `/viewer/{id}` | Return viewer-ready metadata and pose references |
| POST | `/analysis` | Request analysis of caller-provided imported artifacts |
| POST | `/statistics` | Request statistics for existing analysis output |
| POST | `/validation` | Request validation of existing artifacts |
| GET | `/report/{id}` | Retrieve a generated report descriptor |

## Boundary Rules

- The service must not run FlyGym or MuJoCo implicitly.
- The service must not mutate frozen evidence or manuscript artifacts.
- Dataset and rollout identifiers must resolve through manifests, not guessed
  paths.
- A missing or invalid dataset must remain an explicit non-success state.
- Scientific claims remain bounded by the repository's computational scope.

The browser viewer can consume the pose schema in
[`viewer_pose.schema.json`](viewer_pose.schema.json) without requiring this
future service.
