# FAIR Audit

This audit evaluates version 1.0.0 using repository facts only.

| Principle | Status | Repository evidence | Limitations |
| --- | --- | --- | --- |
| Findable | PARTIAL | GitHub repository URL, Release `v1.0.0`, `CITATION.cff`, release notes, artifact inventories | No DOI is declared unless an external archive mints one |
| Accessible | PARTIAL | Source, documentation, evidence JSON, figures, tables, and final artifacts are version-controlled | Long-term access depends on GitHub or a future external archive |
| Interoperable | PARTIAL | Uses common formats: Python, YAML, JSON, CSV, Markdown, PNG, PDF, DOCX | Upstream simulation reproduction depends on FlyGym 2.1.0 and MuJoCo 3.9.0 |
| Reusable | PARTIAL | MIT license, citation metadata, tests, provenance manifests, evidence traceability, scientific-boundary notes | Raw large artifacts are not curated in Git; biological validation is outside repository scope |

## Not Applicable Items

Clinical, diagnostic, patient-data, and biological-sample access criteria are
NOT APPLICABLE because this repository contains computational simulation and
analysis artifacts, not human-subjects data or original biological datasets.
