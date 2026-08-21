# Tutorial

This tutorial uses deterministic synthetic samples. They are not scientific
evidence.

## 1. Create a Synthetic Dataset

```python
dataset = synthetic_behavior_dataset(sample_count=6)
```

## 2. Export and Verify

```python
manifest = create_dataset_manifest(dataset)
DatasetExporter.export(dataset, "results/v2/ai/synthetic.json")
verify_dataset_integrity(dataset, manifest)
```

## 3. Extract Features

```python
features = generate_feature_matrix(dataset)
```

## 4. Analyze

```python
embeddings = behavior_embeddings(features["matrix"])
clusters = kmeans_cluster(features["matrix"])
```

## 5. Report

```python
generate_ai_behavior_report(
    dataset_summary=dataset.as_dict(),
    feature_summary=features,
    analysis_summary=embeddings,
    benchmark_summary=benchmark,
    output_dir="results/v2/ai/report",
)
```
