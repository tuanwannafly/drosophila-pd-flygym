# Research Repository Report

The repository now has explicit anchors for campaigns, datasets, reports,
figures, publication, supplementary material, benchmarks, validation,
reproducibility, templates, and examples. Each anchor documents its intended
provenance requirements and states that it does not create data.

The canonical scientific chain remains in its existing locations:

```text
notebooks -> src/configs/scripts -> results -> docs/report -> dist
```

No existing scientific file was moved. Large/raw artifacts remain governed by
the existing `.gitignore` policy.
