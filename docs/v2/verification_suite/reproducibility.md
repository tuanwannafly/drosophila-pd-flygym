# Reproducibility

The reproducibility check creates two independent workflow instances and
runs the same caller-supplied rollout with the same options. It compares a
stable projection of the returned analysis, statistics, comparison,
Parkinson-analytics, export, and persistence results. Generated timestamps
and transient identifiers are excluded from that comparison.

The check is deterministic software validation. It is not a statistical
replication and does not create new scientific evidence.

For a reproducible run, record the input rollout checksum, repository commit,
browser/runtime version, options, requested stress sizes, and the complete
verification report together.
