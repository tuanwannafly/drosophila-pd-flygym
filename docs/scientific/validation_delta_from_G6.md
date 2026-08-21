# Validation Delta From G6

G6 concluded that the frozen evidence supports reduced walking speed and
partially supports reduced distance-like locomotor output. It also identified
G5 measurement modules as analysis-ready for bout, turning, trajectory, and
optional open-field endpoints, but did not validate those endpoints because raw
rollout arrays were not available in the frozen evidence.

G8 was expected to use the G7 measurement-enabled evidence package to close
part of that gap.

## Delta Summary

No extended endpoint receives an evidence upgrade in this checkout.

| Endpoint family | G6 status | G8 status | Reason |
| --- | --- | --- | --- |
| Walking bouts | NOT_SUPPORTED | NOT_SUPPORTED | No local G7 walking-bout outputs. |
| Pause bouts and pause duration | NOT_SUPPORTED | NOT_SUPPORTED | No local G7 pause-bout outputs or threshold evidence. |
| Walking duty cycle | NOT_SUPPORTED | NOT_SUPPORTED | No local G7 G5-measurement summaries. |
| Yaw rate and turn bouts | NOT_SUPPORTED | NOT_SUPPORTED | No local G7 yaw-rate or turn-bout outputs. |
| Cumulative turning | NOT_SUPPORTED | NOT_SUPPORTED | No local G7 time-resolved turning summaries. |
| Left/right asymmetry | NOT_SUPPORTED | NOT_SUPPORTED | No local G7 yaw-rate outputs and no direct biological mapping. |
| Exploration metrics | NOT_SUPPORTED | NOT_SUPPORTED | No local G7 trajectories with declared virtual open-field geometry. |

## Interpretation

The G8 result is a traceability finding, not a simulation finding. The local
repository has measurement modules and G7 refresh tooling, but the evidence
package required to validate extended phenotypes was not present. A future G8
refresh can reassess these endpoints once the canonical G7 outputs are copied
into the repository or generated in an approved environment.
