# Python Environment

- Target interpreter: Python 3.12.
- Package layout: `src/` with setuptools automatic discovery.
- Installation: `python -m pip install -e .`.
- Test command: `pytest -q -rs -p no:cacheprovider`.
- Compile command: `python -m compileall -q src scripts tests`.

The exact interpreter patch version and installed packages should be copied
from the runtime that produces an evidence report; this file records the
repository target, not an unobserved environment claim.
