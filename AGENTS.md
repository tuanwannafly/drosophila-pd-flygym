# Agent Instructions

These instructions apply to coding agents working in this repository.

## Role

Codex and other agents are implementation and debugging assistants. They are not
scientific decision-makers. Keep software behavior, simulation assumptions,
biological assumptions, and experimentally observed results separate.

## Hard Rules

- Do not call `add_joints()` until explicitly authorized by the project owner.
- Do not assign `fly.skeleton` manually.
- Do not intentionally mutate MJCF during the current pre-materialization phase.
- Do not invent FlyGym APIs.
- Inspect source, signatures, tests, and examples before using unfamiliar FlyGym APIs.
- Use the smallest safe change that satisfies the request.
- Keep scientific assumptions separate from software behavior.
- Do not infer biological conclusions from simulation results alone.
- Do not move to the next research stage without explicit authorization.
- Run relevant tests after changes.
- Always report verified vs unverified behavior.
- Never silently ignore a failed test.

## Current Block 8.12 Invariants

- Python target: 3.12
- FlyGym target: 2.1.0
- MuJoCo target: 3.9.0
- Primary fly object type: `flygym.compose.fly.neuromechfly.NeuroMechFly`
- `fly.skeleton is None`
- `add_joints()` has not been called
- Body segments: 69
- Anatomical joints: 68
- JointDOFs: 204
- Axis order: `AxisOrder.PITCH_ROLL_YAW`
- Pitch DOFs: 68
- Roll DOFs: 68
- Yaw DOFs: 68
- LF leg JointDOFs: 24
- LM leg JointDOFs: 24
- LH leg JointDOFs: 24
- RF leg JointDOFs: 24
- RM leg JointDOFs: 24
- RH leg JointDOFs: 24
- Non-leg JointDOFs: 60
- MJCF body mapping: 69/69
- Missing parent MJCF bodies for JointDOFs: 0
- Missing child MJCF bodies for JointDOFs: 0
- JointDOF to MJCF joint mapping: 0, expected before materialization
- JointDOF to neutral angle mapping: 0, expected before materialization
- Actuator mappings: 0, expected before materialization
- JointDOF names are unique: 204
- JointDOF name round-trip failures: 0

## Development Guidance

Before modifying behavior:

1. Inspect the repository structure.
2. Inspect the relevant FlyGym source/API.
3. Inspect existing notebooks, scripts, tests, and examples.
4. Determine the exact API and side effects.
5. Make the smallest safe change.
6. Run relevant checks.
7. Report what was verified and what remains unverified.

Do not add placeholder Parkinson's disease algorithms or biological claims. Empty
packages and structure-only scaffolding are acceptable during bootstrap.
