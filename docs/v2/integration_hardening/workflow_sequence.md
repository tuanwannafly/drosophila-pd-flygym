# Main Workflow Sequence

1. Receive raw JSON in the existing loader boundary.
2. Validate recognizable FlyGym structure and normalize it.
3. Compute existing rollout statistics.
4. Register the rollout in the experiment workspace.
5. Run quality, feature, segmentation, normalization, outlier and pipeline stages.
6. Run statistical summaries/comparison.
7. Produce visualization strings and export payloads.
8. Save and restore a persistence snapshot.
9. On any post-import failure, restore the pre-import snapshot and return a structured error.
