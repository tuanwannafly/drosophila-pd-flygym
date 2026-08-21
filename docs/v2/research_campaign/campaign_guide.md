# Campaign Guide

A campaign combines:

- roles such as Healthy or Candidate;
- optional progression stages;
- optional virtual interventions;
- optional custom scenarios;
- a parameter grid;
- seeds;
- replicates;
- metadata.

The matrix is generated as the Cartesian product of those dimensions. Empty
optional dimensions are represented as `null` in the experiment plan, preserving
the distinction between "not configured" and an explicit scenario value.

Resumability is provided by `CampaignCheckpoint`, which records completed
experiments, failed experiments, output references, cursor position, and a
checkpoint hash.

The scheduler is deterministic. Re-running matrix generation with the same
config reproduces the same experiment IDs.
