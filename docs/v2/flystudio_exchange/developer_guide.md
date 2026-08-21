# Developer Guide

When modifying the package format:
- Always bump `Version` in `metadata.py` if changing schema.
- Implement corresponding fallback logic in `Migration.migrate()`.
- Ensure `PackageValidator` captures missing keys explicitly.
- The format must remain independent of MuJoCo and FlyGym entirely.
