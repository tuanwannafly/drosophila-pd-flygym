# Tutorial

You can generate the default demo packages using the CLI:
```bash
python scripts/build_demo_project.py
```
This generates `healthy.flystudio`, `candidate.flystudio`, and `comparison.flystudio`.

To export an arbitrary layout:
```bash
python scripts/export_flystudio_project.py "My Custom Project" "custom.flystudio"
```

To validate an exported package before uploading to the Web Platform:
```bash
python scripts/import_flystudio_project.py "custom.flystudio"
```
