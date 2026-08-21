# Historical Session Inventory

## Scope

This document is the Phase G1 inventory for the historical research
notebooks that are currently present in the repository. The notebooks were
read as JSON, including code cells, markdown, and stored outputs. They were
not executed. Stored notebook outputs are historical execution records; they
are not a substitute for the frozen repository evidence reports.

The repository contains exactly two historical Session notebooks. No
Session 03-10 notebook is present, and no placeholder notebooks were created.

The protected file
`notebooks/session_02_healthy_baseline/Session_02_Healthy_Baseline.ipynb`
was read but not modified, staged, reverted, or cleaned.

## Notebooks Reviewed

| Session | Path | Cells | Historical role | Repository history |
| --- | --- | ---: | --- | --- |
| 01 | `notebooks/session_01_environment/FlyBrain_Session01_Setup.ipynb` | 29 | Colab, FlyGym, MuJoCo, GPU, fly/world/simulation setup | Created in `10e475d`; organized with Session 02 in `1de7c8b` |
| 02 | `notebooks/session_02_healthy_baseline/Session_02_Healthy_Baseline.ipynb` | 85 | Environment reconstruction, attachment diagnostics, anatomy audits, Blocks 8.12-8.19 | Created in `b5d3e85`; organized with Session 01 in `1de7c8b` |

All code cells had stored outputs. Session 01 contains one stored image cell;
Session 02 contains seven stored image cells. The images and outputs remain in
the notebooks and were not regenerated.

## Block Inventory

### Session 01

| Blocks/cells | Classification | Scientific or engineering purpose | Current disposition |
| --- | --- | --- | --- |
| Block 1, cells 1-2 | HISTORICAL_SETUP | Establish Colab, EGL, and GPU visibility. | Environment assumptions are documented; no standalone source module replaces this cell pair. |
| Block 2, cells 3-4 | HISTORICAL_SETUP | Install FlyGym v2.1.0 and supporting packages. | Colab setup remains an execution concern; the version is recorded in evidence provenance. |
| Block 3, cells 5-6 | API_CHECK | Import FlyGym, `Simulation`, and `NeuroMechFly`. | API facts are represented by the canonical audit and baseline imports. |
| Block 4, cells 7-9 | REUSABLE_SETUP | Instantiate a named `NeuroMechFly` and identify the default body model. | The construction idea is reused by anatomy audits and the baseline pipeline. |
| Block 5, cells 10-11 | REUSABLE_SETUP | Create `FlatGroundWorld`. | Reused by `src/drosophila_pd/experiments/healthy_baseline.py` and Milestone C. |
| Block 6, cells 12-13 | DIAGNOSTIC | Inspect an empty world before fly registration. | Redundant for the canonical baseline and not an evidence-producing invariant. |
| Block 8, cells 14-15 | MATERIALIZATION_AND_SETUP | Build a legs-only skeleton, call `add_joints()`, add 42 position actuators and six adhesion actuators, add a camera, and attach the fly. | Replaced by the explicit Milestone 8B materialization gate plus the separate Milestone C baseline pipeline. |
| Workflow / Block 7, cells 16-18 | REUSABLE_SETUP | Compile the attached world through `Simulation`. | Reused by the canonical healthy-baseline runner; not part of the 8B pre/post anatomy-only milestone. |
| Fly/world checks, cells 20-23 | DIAGNOSTIC | Validate names, active DOFs, world registration, MJCF counts, and compiled model counts. | The relevant checks were narrowed into canonical Milestone C metrics and 8B invariants. |
| Block 9, cells 24-27 | OPTIONAL_RUNTIME | Install and verify Warp/CUDA for accelerated rendering or execution. | Not required for CPU numerical baseline validation; no frozen evidence depends on this GPU check. |
| Block 10, cell 28 | INFRASTRUCTURE | Mount Google Drive and create a project directory. | Colab convenience only; not part of the repository workflow. |

### Session 02

| Blocks/cells | Classification | Scientific or engineering purpose | Current disposition |
| --- | --- | --- | --- |
| Block 1, cells 2-4 | HISTORICAL_SETUP | Initialize the Colab session and inspect the runtime. | Historical setup; current provenance is emitted by repository scripts. |
| Block 1.2, cells 5-6 | HISTORICAL_SETUP | Install MuJoCo and FlyGym 2.1.0. | Historical setup; current Colab commands are documented in `docs/report/reproducibility.md`. |
| Block 2, cells 7-9 | API_CHECK | Load/reconstruct the Session 01 environment and inspect available APIs. | Replaced by canonical scripts and tests; useful as API discovery history. |
| Block 3, cells 10-11 | REUSABLE_SETUP | Recreate the healthy `NeuroMechFly`. | The construction concept is reused by the anatomy and baseline implementations. |
| Block 4, cells 12-13 | REUSABLE_SETUP | Create `FlatGroundWorld`. | Reused by Milestone C. |
| Blocks 5-5.2, cells 14-18 | REUSABLE_SETUP_AND_DIAGNOSTIC | Discover `Rotation3D`, repair a rotation invocation, and attach the fly to the world. | The verified `world.add_fly()` pattern is reused by Milestone C; exploratory retries are not canonical. |
| Block 5.3, cells 20-22 | DIAGNOSTIC | Inspect ground-contact configuration and disable contact sensors during attachment. | The configuration choice is reused by the baseline runner; source-tracing cells are historical diagnostics. |
| Blocks 6-7.2, cells 23-36 | DEBUG_AND_SOURCE_TRACE | Diagnose attached MjSpec structure, compile behavior, ground-sensor references, and FlyGym attachment internals. | The attachment semantics informed the canonical pipeline, but failed compile probes and repeated rebuilds were discarded. |
| Blocks 8.1-8.5, cells 38-50 | DEBUG_AND_SOURCE_TRACE | Inspect MjSpec, body navigation, and the construction path from `NeuroMechFly` through `BaseFly` to MjSpec. | The concise source/API facts were retained in the 8.12/8.13 audits; navigation experiments were not. |
| Blocks 8.6-8.8, cells 51-61 | STRUCTURAL_DISCOVERY | Establish the relationship between the local skeleton, `JointDOF`s, and MjSpec body structure. | Replaced by the canonical 8.12 audit and the 8B materialization state transition. |
| Blocks 8.9-8.11, cells 62-65 | STRUCTURAL_DISCOVERY | Discover the skeleton API, count 204 JointDOFs, and verify `PITCH_ROLL_YAW` axis order. | Canonicalized in `src/drosophila_pd/anatomy/audit.py`; frozen in Block 8.12 evidence. |
| Block 8.12, cells 66-68 | READ_ONLY | Audit pre-materialization body, JointDOF, axis, name-round-trip, and empty mapping invariants. | Replaced by `anatomy/audit.py`, `scripts/audit_block_8_12.py`, and `results/baseline/block_8_12_audit.json`. |
| Block 8.13, cells 69-69 | READ_ONLY | Inspect class/MRO, joint APIs, MjSpec/root objects, mappings, and the `add_joints()` materialization boundary without calling it. | Replaced by `anatomy/orientation.py`, `scripts/audit_block_8_13.py`, and `results/baseline/block_8_13_orientation.json`. |
| Blocks 8.14-8.15, cells 70-72 | READ_ONLY | Compare a local base skeleton with expected MJCF body/joint structure and verify 69 bodies, 68 anatomical joints, and 204 DOFs. | Superseded by the canonical Milestone 8B pre-materialization audit and evidence. |
| Block 8.16, cells 74-76 | READ_ONLY_SOURCE_AUDIT | Inspect the source and signature of `add_joints()` and its joint-creation path. | Its verified boundary became the only materialization call in `anatomy/materialization.py`; the notebook itself did not call it. |
| Block 8.17, cells 77-78 | READ_ONLY_SOURCE_AUDIT | Inspect the `add_actuators()` path and actuator mapping behavior. | Retained as a no-actuator invariant in 8B; actuator construction belongs to Milestone C. |
| Block 8.18, cells 79-80 | READ_ONLY | Compare existing MJCF joints with skeleton JointDOFs before materialization. | Superseded by the 8B pre/post comparison; frozen 8B confirms zero pre-joints and 204 post-joints. |
| Block 8.19A, cells 81-82 | READ_ONLY_API_DISCOVERY | Discover skeleton traversal APIs and recheck the pre-materialization state. | Superseded by compact canonical helpers. |
| Block 8.19B, cells 83-84 | READ_ONLY | Recheck body, anatomical-joint, JointDOF, axis, and body-mapping invariants. | Superseded by canonical Milestone 8B validation. |

## Canonical Traceability Chain

The supported repository relationship is:

```text
Session 01 setup ideas
    -> anatomy audit / explicit materialization / healthy baseline modules
Session 02 anatomy blocks 8.12-8.19
    -> Block 8.12, Block 8.13, Milestone 8B canonical audits
canonical runners
    -> frozen evidence JSON under results/
frozen evidence
    -> final_report.md and report traceability/reproducibility documentation
```

The row-level mapping is in `canonical_mapping.csv`. The YAML files preserve
the notebook-oriented view, including classifications and known discarded or
reusable logic. A missing evidence or manuscript mapping is recorded as
`none`; it is not inferred from similar-looking output.

## Evidence and Traceability Gaps

- Notebook outputs are not cryptographically linked to individual cells or
  cell execution IDs in the frozen evidence reports.
- Session 01 has no direct evidence JSON of its own; its outputs are
  historical setup evidence and the later canonical reports are the
  reproducible record.
- Session 02 contains no completed canonical locomotion baseline; its early
  compile probes are diagnostics, not Milestone C evidence.
- The final manuscript and evidence traceability document summarize the
  frozen milestones, but do not provide a row for every historical Block
  8.13-8.19 cell.
- Sessions 03-10 have no notebooks in this repository, so no notebook-level
  traceability can be asserted for them.

## Phase G1 Boundary

This inventory does not alter the scientific implementation, evidence, or
manuscript. It records where historical work was replaced, where it remains
useful as a documented API observation, and where the repository has no
supporting artifact.
