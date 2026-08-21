# Experiment Reproduction

1. Clone or pull the repository from GitHub.
2. Check out the intended commit or release tag.
3. Create a Python 3.12 environment and install `-e .`.
4. Install `-e ".[simulation]"` only for an authorized FlyGym/MuJoCo run.
5. Verify configuration paths, seed, duration, timestep, and output path.
6. Run the exact milestone command documented in `PROJECT_CONTEXT.md`.
7. Record Python, FlyGym, MuJoCo, OS, seed, commit, and output hashes.
8. Compare the result against the corresponding frozen schema and evidence.

The final report can be rebuilt independently with
`python scripts/build_final_report.py`; it does not rerun simulations.
