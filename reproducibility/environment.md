# Environment

## Declared stack

| Component | Declared target |
| --- | --- |
| Python | 3.12 |
| FlyGym | 2.1.0 |
| MuJoCo | 3.9.0 |
| Execution environment | Google Colab for simulation reproduction |
| Source of truth | GitHub repository |

The root package and CPU-only evidence-analysis commands do not import FlyGym
at package import time. Simulation reproduction requires the optional
`simulation` dependency set and the documented compatible environment.
