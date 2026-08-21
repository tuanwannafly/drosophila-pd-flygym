# FAIR Principles

This note summarizes how repository version 1.0.0 supports the FAIR principles
using repository facts only.

## Findable

The repository has a stable GitHub URL, Release `v1.0.0`, `CITATION.cff`,
release notes, and explicit artifact inventories. A DOI is not declared unless
an external archive mints one.

## Accessible

The curated source, documentation, evidence JSON, figures, tables, and final
report artifacts are stored in the repository. Access depends on GitHub or any
future external archive chosen by the project owner.

## Interoperable

Reusable artifacts use common formats: Python, YAML, JSON, CSV, Markdown, PNG,
PDF, and DOCX. The simulation stack is explicitly documented as Python 3.12.13,
FlyGym 2.1.0, and MuJoCo 3.9.0 for frozen Colab evidence.

## Reusable

The repository includes an MIT license, citation metadata, release notes,
tests, provenance manifests, evidence traceability, and scientific-boundary
statements. Reuse remains bounded by the availability of compatible FlyGym and
MuJoCo environments for upstream simulation reproduction.
