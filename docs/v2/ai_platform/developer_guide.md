# Developer Guide

## Rules

- Keep the platform additive.
- Preserve backward compatibility with earlier v2 modules.
- Do not run simulations from AI modules.
- Do not write disease claims into labels, examples, or reports.
- Keep synthetic examples clearly marked.

## Optional Columnar Formats

Parquet and Arrow support uses optional `pyarrow`. When the dependency is not
installed, loaders and exporters raise a clear runtime error.

## Future Backends

Classifier and embedding APIs are designed to accept future ML backends. The
current implementation is deterministic and dependency-free apart from NumPy
and Matplotlib.
