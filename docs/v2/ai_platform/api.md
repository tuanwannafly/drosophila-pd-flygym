# API

## Dataset

```python
from drosophila_pd.behavior_platform import (
    DatasetExporter,
    DatasetLoader,
    create_dataset_manifest,
    synthetic_behavior_dataset,
)

dataset = synthetic_behavior_dataset()
manifest = create_dataset_manifest(dataset)
DatasetExporter.export(dataset, "results/v2/ai/dataset.json")
loaded = DatasetLoader.load("results/v2/ai/dataset.json")
```

## Features

```python
from drosophila_pd.behavior_platform import generate_feature_matrix

feature_matrix = generate_feature_matrix(dataset)
```

## Unsupervised Analysis

```python
from drosophila_pd.behavior_platform import pca_embedding, kmeans_cluster

embedding = pca_embedding(feature_matrix["matrix"])
clusters = kmeans_cluster(feature_matrix["matrix"], n_clusters=3)
```

## Classification

```python
from drosophila_pd.behavior_platform import classify_feature_matrix

report = classify_feature_matrix(
    feature_matrix,
    classifier="rule_based",
    rules={"moving": {"speed_mean_mm_s": 1.0}},
)
```
