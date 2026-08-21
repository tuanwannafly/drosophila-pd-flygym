# Dataset Requirements

The future package must follow
[`dataset_specification.md`](../../../research/campaigns/parkinson_study/dataset_specification.md)
and validate against the Project B manifest schema.

Required before execution:

- dataset type `pd` as a computational category;
- semantic dataset version;
- approved computational configuration and full source provenance;
- manifest, metadata, declared trajectory files, frame counts, and checksums;
- deterministic experiment seed and timing metadata;
- explicit limitations and scientific boundary.

No missing file is synthesized and no unsupported observable is inferred.
