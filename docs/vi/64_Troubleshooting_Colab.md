# Troubleshooting Colab

## Package import fails

Restart the runtime, run notebook 00, and verify Python 3.12, FlyGym 2.1.0
and MuJoCo 3.9.0.

## Asset or mesh error

Read the first missing asset path and rerun setup in a clean runtime. Do not
edit frozen repository assets.

## WAITING_DATASET

The manifest-backed dataset is absent. Run notebook 05 or place an approved
dataset at the documented path.

## INVALID_DATASET

Inspect the exact missing file, schema, frame count or checksum finding. Do not
force a pass by changing the report.

## Pipeline failure

Keep the emitted error and stage output. A computational pipeline failure is
not evidence of a biological result.
