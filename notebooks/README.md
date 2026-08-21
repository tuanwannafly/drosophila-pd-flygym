# Research Notebooks

These notebooks are research interfaces and historical execution records. They
are useful for exploring ideas, preserving session context, and running workflows
in Google Colab.

Reusable logic belongs in `src/drosophila_pd`. Future notebooks should import
project code instead of duplicating audit, controller, perturbation, or metrics
logic inline.

Google Colab is an execution environment. GitHub remains the source of truth for
code, tests, configuration, and documentation. Future sessions should be
reproducible from a fresh runtime by installing the repository requirements,
importing project code, and writing small metadata/results artifacts.

Historical notebook output records what happened in a previous runtime. It is
not the same thing as a current reproducible repository result. Current
reproducibility should be established by rerunning the relevant project code,
for example `scripts/audit_block_8_12.py`.

## Session Roadmap

- `session_01_environment/` - Environment, FlyGym, and MuJoCo setup
- `session_02_healthy_baseline/` - Healthy baseline
- `session_03_neural_perturbation/` - Neural perturbation
- `session_04_phenotype_screen/` - Phenotype screen
- `session_05_lod_dof_analysis/` - LOD / DOF analysis
- `session_06_bootstrap/` - Bootstrap
- `session_07_disease_model/` - Disease model
- `session_08_parkinson_controller/` - Parkinson controller
- `session_09_3d_validation/` - 3D validation
- `session_10_video_figures/` - Video / figures
