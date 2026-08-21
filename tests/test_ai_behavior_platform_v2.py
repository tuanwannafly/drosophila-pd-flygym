from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.behavior_platform import (  # noqa: E402
    AI_PLATFORM_SCOPE,
    BehaviorSample,
    BehaviorSequenceDataset,
    BenchmarkCase,
    DatasetExporter,
    DatasetLoader,
    analytics_panel_inventory,
    behavior_embeddings,
    build_ai_analytics_dashboard,
    build_behavior_index,
    classify_feature_matrix,
    create_dataset_manifest,
    dbscan_cluster,
    distance_based_classifier,
    export_ai_analytics_dashboard,
    export_benchmark_report,
    extract_behavior_features,
    generate_ai_behavior_report,
    generate_feature_matrix,
    hierarchical_cluster,
    kmeans_cluster,
    nearest_neighbors,
    pca_embedding,
    plugin_classifier,
    rule_based_classifier,
    run_behavior_benchmark,
    similarity_search,
    spectral_cluster,
    standardize_features,
    synthetic_behavior_dataset,
    tsne_embedding,
    umap_embedding,
    verify_dataset_integrity,
)


def test_dataset_framework_json_csv_npz_manifest_index_and_integrity(tmp_path):
    dataset = synthetic_behavior_dataset(sample_count=4, sample_length=12)
    assert dataset.as_dict()["scientific_scope"] == AI_PLATFORM_SCOPE
    assert dataset.metadata["scientific_evidence"] is False
    sequence = BehaviorSequenceDataset(dataset, tuple(sample.sample_id for sample in dataset.samples))
    assert sequence.as_dict()["sequence_order"][0] == "synthetic_00"

    index = build_behavior_index(dataset)
    assert "Healthy" in index.conditions
    assert "synthetic" in index.labels
    manifest = create_dataset_manifest(dataset)
    assert verify_dataset_integrity(dataset, manifest) is True
    changed = synthetic_behavior_dataset(sample_count=3, sample_length=12)
    assert verify_dataset_integrity(changed, manifest) is False

    json_path = DatasetExporter.export(dataset, tmp_path / "dataset.json")
    csv_path = DatasetExporter.export(dataset, tmp_path / "dataset.csv")
    npz_path = DatasetExporter.export(dataset, tmp_path / "dataset.npz")
    assert DatasetLoader.load(json_path).dataset_id == dataset.dataset_id
    assert DatasetLoader.load(csv_path).samples[0].sample_id == "synthetic_00"
    assert DatasetLoader.load(npz_path).samples[1].condition == "Candidate"
    with pytest.raises(ValueError, match="unsupported"):
        DatasetExporter.export(dataset, tmp_path / "dataset.bad", format="bad")
    with pytest.raises(ValueError, match="unsupported"):
        DatasetLoader.load(tmp_path / "dataset.bad", format="bad")


def test_optional_parquet_arrow_paths_are_supported_or_report_dependency(tmp_path):
    dataset = synthetic_behavior_dataset(sample_count=2, sample_length=8)
    for fmt in ("parquet", "arrow"):
        path = tmp_path / f"dataset.{fmt}"
        try:
            DatasetExporter.export(dataset, path, format=fmt)
            loaded = DatasetLoader.load(path, format=fmt)
            assert loaded.samples[0].sample_id == "synthetic_00"
        except RuntimeError as exc:
            assert "pyarrow is required" in str(exc)


def test_feature_extraction_and_matrix_generation():
    dataset = synthetic_behavior_dataset(sample_count=5, sample_length=16)
    features = extract_behavior_features(dataset.samples[0])
    assert features["trajectory_path_length_mm"] > 0
    assert features["speed_mean_mm_s"] > 0
    assert features["acceleration_abs_mean_mm_s2"] >= 0
    assert features["jerk_abs_mean_mm_s3"] >= 0
    assert features["contact_duty_factor"] == pytest.approx(0.5)
    assert features["behavior_episode_count"] > 0

    matrix = generate_feature_matrix(dataset)
    assert matrix["finite"] is True
    assert len(matrix["sample_ids"]) == 5
    assert "speed_mean_mm_s" in matrix["feature_names"]
    subset = generate_feature_matrix(dataset, feature_names=("speed_mean_mm_s", "tortuosity"))
    assert np.asarray(subset["matrix"]).shape == (5, 2)

    with pytest.raises(ValueError, match="positions"):
        extract_behavior_features(BehaviorSample("bad", "Custom", arrays={}))
    with pytest.raises(ValueError, match="timestep_s"):
        extract_behavior_features(
            BehaviorSample(
                "bad_time",
                "Custom",
                arrays={"thorax_positions": np.zeros((3, 3))},
                metadata={"timestep_s": 0.0},
            )
        )
    with pytest.raises(ValueError, match="shape"):
        extract_behavior_features(
            BehaviorSample("bad_shape", "Custom", arrays={"thorax_positions": np.zeros((3, 1))})
        )


def test_feature_extraction_alternate_inputs_and_edge_cases():
    sample = BehaviorSample(
        "alternate",
        "Custom",
        arrays={
            "positions": np.array([[0.0, 0.0], [0.0, 0.0], [1.0, 0.0]]),
            "yaw": np.array([0.0, 0.0, 0.2]),
        },
        metadata={"timestep_s": 0.5},
    )
    features = extract_behavior_features(sample)
    assert features["contact_duty_factor"] == 0.0
    assert features["behavior_episode_count"] == 0.0
    assert features["yaw_abs_rate_mean_rad_s"] > 0

    single = BehaviorSample(
        "single",
        "Custom",
        arrays={"positions": np.array([[0.0, 0.0]])},
        metadata={"timestep_s": 1.0},
    )
    single_features = extract_behavior_features(single)
    assert single_features["speed_mean_mm_s"] == 0.0
    assert single_features["curvature_abs_mean_rad_per_mm"] == 0.0


def test_unsupervised_analysis_embeddings_clusters_and_search():
    matrix = np.asarray(generate_feature_matrix(synthetic_behavior_dataset(sample_count=6))["matrix"], dtype=float)
    assert standardize_features(matrix).shape == matrix.shape
    pca = pca_embedding(matrix)
    assert pca["method"] == "PCA"
    assert len(pca["embedding"]) == 6
    assert umap_embedding(matrix)["method"].startswith("UMAP")
    assert tsne_embedding(matrix)["method"].startswith("TSNE")
    embeddings = behavior_embeddings(matrix)
    assert set(embeddings) == {"PCA", "UMAP", "tSNE"}

    assert len(kmeans_cluster(matrix, n_clusters=3)["labels"]) == 6
    assert dbscan_cluster(matrix, eps=10.0, min_samples=1)["cluster_count"] >= 1
    assert len(hierarchical_cluster(matrix, n_clusters=2)["labels"]) == 6
    assert len(spectral_cluster(matrix, n_clusters=2)["labels"]) == 6
    assert nearest_neighbors(matrix, query_index=0, k=2)["neighbors"][0]["index"] != 0
    assert similarity_search(matrix, query_vector=matrix[0], k=2)["neighbors"][0]["index"] == 0

    with pytest.raises(ValueError, match="feature matrix"):
        standardize_features([])
    with pytest.raises(ValueError, match="finite"):
        standardize_features([[float("nan")]])
    with pytest.raises(ValueError, match="query_vector"):
        similarity_search(matrix, query_vector=[1.0])


def test_classification_rule_distance_plugin_and_matrix_api():
    dataset = synthetic_behavior_dataset(sample_count=3)
    feature_matrix = generate_feature_matrix(dataset)
    features = extract_behavior_features(dataset.samples[0])
    rules = {"moving": {"speed_mean_mm_s": 1.0}, "slow": {"freezing_fraction": 0.5}}
    rule = rule_based_classifier("s0", features, rules=rules)
    assert rule.label in rules
    assert sum(rule.probabilities.values()) == pytest.approx(1.0)

    prototypes = {
        "healthy_like": features,
        "low_speed": {"speed_mean_mm_s": 0.0, "trajectory_path_length_mm": 0.0},
    }
    distance = distance_based_classifier("s0", features, prototypes=prototypes)
    assert distance.label == "healthy_like"
    plugin = plugin_classifier("s0", features, plugin=lambda values: ("custom", 0.75))
    assert plugin.confidence == pytest.approx(0.75)
    report = classify_feature_matrix(feature_matrix, classifier="rule_based", rules=rules)
    assert report["label_counts"]
    report = classify_feature_matrix(feature_matrix, classifier="distance_based", prototypes=prototypes)
    assert len(report["results"]) == 3
    with pytest.raises(ValueError, match="at least one label"):
        rule_based_classifier("s0", features, rules={})
    with pytest.raises(ValueError, match="unsupported"):
        classify_feature_matrix(feature_matrix, classifier="future_backend")


def test_benchmark_report_generation_and_exports(tmp_path):
    cases = [
        BenchmarkCase("healthy", "Healthy", {"speed": 1.0, "coverage": 0.8}),
        BenchmarkCase("candidate", "Candidate", {"speed": 0.8, "coverage": 0.7}),
        BenchmarkCase("intervention", "Intervention", {"speed": 0.9, "coverage": 0.75}),
    ]
    report = run_behavior_benchmark(cases)
    assert report["benchmark_report"]["case_count"] == 3
    assert report["leaderboard"][0]["case_id"] == "healthy"
    files = export_benchmark_report(report, tmp_path / "benchmark")
    assert all(path.exists() and path.stat().st_size > 0 for path in files.values())
    with pytest.raises(ValueError, match="at least one"):
        run_behavior_benchmark([])


def test_automatic_report_and_interactive_analytics(tmp_path):
    dataset = synthetic_behavior_dataset(sample_count=4)
    feature_matrix = generate_feature_matrix(dataset)
    embedding = pca_embedding(feature_matrix["matrix"])
    cluster = kmeans_cluster(feature_matrix["matrix"])
    benchmark = run_behavior_benchmark(
        [
            BenchmarkCase(sample.sample_id, sample.condition, {"speed": row[feature_matrix["feature_names"].index("speed_mean_mm_s")]})
            for sample, row in zip(dataset.samples, feature_matrix["matrix"])
        ]
    )
    analytics = build_ai_analytics_dashboard(
        dataset_summary=dataset.as_dict(),
        embedding_report=embedding,
        clustering_report=cluster,
        comparison_report=benchmark,
    )
    assert "cluster_explorer" in analytics["panels"]
    assert "dataset_explorer" in analytics_panel_inventory()
    html = export_ai_analytics_dashboard(analytics, tmp_path / "analytics.html")
    assert html.exists() and "AI Behavior Analytics" in html.read_text(encoding="utf-8")

    files = generate_ai_behavior_report(
        dataset_summary=dataset.as_dict(),
        feature_summary=feature_matrix,
        analysis_summary=analytics,
        benchmark_summary=benchmark,
        output_dir=tmp_path / "report",
        formats=("markdown", "html", "pdf", "json", "csv"),
    )
    assert set(files) == {"plot_png", "markdown", "html", "pdf", "json", "csv"}
    assert all(path.exists() and path.stat().st_size > 0 for path in files.values())
    assert "AI Behavioral Analysis Report" in files["markdown"].read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported"):
        generate_ai_behavior_report(
            dataset_summary=dataset.as_dict(),
            feature_summary=feature_matrix,
            analysis_summary=analytics,
            benchmark_summary=benchmark,
            output_dir=tmp_path / "bad",
            formats=("docx",),
        )
    with pytest.raises(ValueError, match="at least one"):
        generate_ai_behavior_report(
            dataset_summary=dataset.as_dict(),
            feature_summary=feature_matrix,
            analysis_summary=analytics,
            benchmark_summary=benchmark,
            output_dir=tmp_path / "bad_empty",
            formats=(),
        )


def test_synthetic_dataset_validation_errors_and_sample_roundtrip():
    with pytest.raises(ValueError, match="sample_count"):
        synthetic_behavior_dataset(sample_count=0)
    sample = synthetic_behavior_dataset(sample_count=1).samples[0]
    roundtrip = BehaviorSample.from_dict(sample.as_dict())
    assert roundtrip.sample_id == sample.sample_id
    assert roundtrip.metadata["scientific_evidence"] is False
