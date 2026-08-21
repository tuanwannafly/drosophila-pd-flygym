# Quick Start

## Install

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`; on
Linux/macOS, use `source .venv/bin/activate`.

## Check the package

```bash
python -m drosophila_pd
pytest -q -rs -p no:cacheprovider
```

## Reproduce frozen evidence

Use the commands in the root README and the milestone-specific sections of
`PROJECT_CONTEXT.md`. FlyGym/MuJoCo commands require the documented Colab
environment. CPU-only analysis and report packaging do not require simulation
dependencies.
