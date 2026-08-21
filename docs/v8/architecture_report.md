# Architecture Report

V8 adds a context, session, event log, output persistence, summary, and runtime
package plus a thin CLI. The only scientific integration point is the existing
`StudyOrchestrator`.
