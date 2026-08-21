# Extension Guide

## New Features

Add feature families in `ai_features.py` and include stable names in generated
feature matrices.

## New Models

Wrap future ML backends behind functions that return JSON-friendly reports with
labels, probabilities, confidence, and metadata.

## New Export Formats

Add exporters through `DatasetExporter` and `generate_ai_behavior_report()`.
Avoid changing existing output schemas unless a new version field is added.
