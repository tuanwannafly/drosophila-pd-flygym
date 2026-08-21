# V7 Architecture

V7 adds five small intake responsibilities: dataset model/discovery, rollout
location and frame inspection, metadata loading, integrity validation, and
manifest-view construction. `dataset_cli.py` is a thin command adapter.

The current filesystem has no `datasets/<type>/<version>/manifest.json` with
real payloads. Therefore discovery returns `WAITING_DATASET`, validation has
no dataset to validate, and the execution pipeline is not called.

The scientific boundary is unchanged: imported computational rollout data is
not automatically biological evidence, Parkinson's disease validation, or a
mechanistic claim.
