# Quality Control

Quality reports identify missing channels, non-finite values, range violations, channel-length inconsistencies, duplicate frame indices, and large trajectory jumps. Findings are separated into warnings and errors, with suggestions for repair or inspection.

Quality checks do not delete, repair, or rewrite source rollout data. A pipeline consumer decides whether a report with warnings is suitable for a downstream analysis.
