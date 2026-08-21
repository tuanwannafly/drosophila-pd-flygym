# Limitations

- Open-field metrics depend on the virtual arena definition supplied by the
  caller.
- Custom zones currently support circular and rectangular regions.
- Dashboard HTML export is a portable summary, not a hosted interactive app.
- GIF and MP4 export require an optional `imageio` backend; PNG sequence export
  is the deterministic fallback.
- Computational progression stages do not encode biology.
- Biological interpretation requires a separate evidence-mapping layer.
