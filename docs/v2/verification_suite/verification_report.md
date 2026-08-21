# End-to-End Verification Report

## Scope

The expected software path is:

`Import -> Normalize -> Quality Control -> Features -> Analysis -> Statistics -> Comparison -> Parkinson analytics -> Visualization -> Report -> Export -> Workspace persistence`

`VerificationSuite.verifyRollout()` checks that the existing
`IntegrationWorkflow.importRollout()` returns these stages in order, has no
analysis errors, produces finite analysis/statistical values, produces all
four export formats, and passes the persistence round trip.

This is software verification only. It does not establish biological
validation, diagnosis, disease severity, dopamine equivalence, or mechanism.

## Input policy

The suite requires a real rollout supplied by the caller. The repository's
frozen evidence reports contain summaries rather than raw rollout arrays, so
they are not silently treated as rollout input. A run without raw rollout
input must be reported as blocked or incomplete.

Invalid input is checked separately: it must be rejected and leave the
workflow in its previous state.
