"""Deterministic unsupervised analysis for behavior feature matrices."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np


def standardize_features(matrix: Sequence[Sequence[float]]) -> np.ndarray:
    """Return z-scored features with zero-variance columns preserved."""

    values = _matrix(matrix)
    mean = np.mean(values, axis=0)
    std = np.std(values, axis=0)
    std[std == 0] = 1.0
    return (values - mean) / std


def pca_embedding(matrix: Sequence[Sequence[float]], *, n_components: int = 2) -> dict[str, Any]:
    """Compute PCA using singular value decomposition."""

    values = standardize_features(matrix)
    components = max(1, min(int(n_components), values.shape[0], values.shape[1]))
    _, singular, vh = np.linalg.svd(values, full_matrices=False)
    embedding = values @ vh[:components].T
    total = float(np.sum(singular**2))
    variance = (singular[:components] ** 2 / total).tolist() if total else [0.0] * components
    return {
        "method": "PCA",
        "embedding": embedding.tolist(),
        "components": vh[:components].tolist(),
        "explained_variance_ratio": variance,
    }


def umap_embedding(matrix: Sequence[Sequence[float]], *, n_components: int = 2) -> dict[str, Any]:
    """Return a deterministic UMAP-compatible embedding approximation."""

    result = pca_embedding(matrix, n_components=n_components)
    result["method"] = "UMAP_COMPATIBLE_PCA_INITIALIZATION"
    result["note"] = "Deterministic dependency-free embedding for UMAP-compatible workflows."
    return result


def tsne_embedding(matrix: Sequence[Sequence[float]], *, n_components: int = 2) -> dict[str, Any]:
    """Return a deterministic t-SNE-compatible embedding approximation."""

    result = pca_embedding(matrix, n_components=n_components)
    result["method"] = "TSNE_COMPATIBLE_PCA_INITIALIZATION"
    result["note"] = "Deterministic dependency-free embedding for t-SNE-compatible workflows."
    return result


def kmeans_cluster(
    matrix: Sequence[Sequence[float]],
    *,
    n_clusters: int = 2,
    max_iter: int = 50,
) -> dict[str, Any]:
    """Cluster samples with deterministic k-means."""

    values = standardize_features(matrix)
    k = max(1, min(int(n_clusters), values.shape[0]))
    centroids = values[:k].copy()
    labels = np.zeros(values.shape[0], dtype=int)
    for _ in range(max_iter):
        distances = _distance_matrix(values, centroids)
        new_labels = np.argmin(distances, axis=1)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for cluster in range(k):
            members = values[labels == cluster]
            if members.size:
                centroids[cluster] = np.mean(members, axis=0)
    return {"method": "KMeans", "labels": labels.tolist(), "centroids": centroids.tolist()}


def dbscan_cluster(
    matrix: Sequence[Sequence[float]],
    *,
    eps: float = 1.0,
    min_samples: int = 2,
) -> dict[str, Any]:
    """Cluster samples with a compact deterministic DBSCAN implementation."""

    values = standardize_features(matrix)
    distances = _distance_matrix(values, values)
    labels = np.full(values.shape[0], -1, dtype=int)
    visited = np.zeros(values.shape[0], dtype=bool)
    cluster_id = 0
    for index in range(values.shape[0]):
        if visited[index]:
            continue
        visited[index] = True
        neighbors = np.where(distances[index] <= eps)[0].tolist()
        if len(neighbors) < min_samples:
            continue
        labels[index] = cluster_id
        queue = list(neighbors)
        while queue:
            point = queue.pop(0)
            if not visited[point]:
                visited[point] = True
                point_neighbors = np.where(distances[point] <= eps)[0].tolist()
                if len(point_neighbors) >= min_samples:
                    queue.extend(n for n in point_neighbors if n not in queue)
            if labels[point] == -1:
                labels[point] = cluster_id
        cluster_id += 1
    return {"method": "DBSCAN", "labels": labels.tolist(), "cluster_count": cluster_id}


def hierarchical_cluster(matrix: Sequence[Sequence[float]], *, n_clusters: int = 2) -> dict[str, Any]:
    """Agglomerative clustering with average linkage."""

    values = standardize_features(matrix)
    clusters = [{index} for index in range(values.shape[0])]
    merges = []
    while len(clusters) > max(1, n_clusters):
        best = (float("inf"), 0, 1)
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                distance = np.mean([np.linalg.norm(values[a] - values[b]) for a in clusters[i] for b in clusters[j]])
                if distance < best[0]:
                    best = (float(distance), i, j)
        _, i, j = best
        merges.append({"left": sorted(clusters[i]), "right": sorted(clusters[j]), "distance": best[0]})
        clusters[i] = clusters[i] | clusters[j]
        del clusters[j]
    labels = np.zeros(values.shape[0], dtype=int)
    for label, cluster in enumerate(clusters):
        for index in cluster:
            labels[index] = label
    return {"method": "Hierarchical", "labels": labels.tolist(), "merges": merges}


def spectral_cluster(matrix: Sequence[Sequence[float]], *, n_clusters: int = 2) -> dict[str, Any]:
    """Dependency-free spectral clustering via similarity eigenvectors and k-means."""

    values = standardize_features(matrix)
    distances = _distance_matrix(values, values)
    sigma = np.median(distances[distances > 0]) if np.any(distances > 0) else 1.0
    affinity = np.exp(-(distances**2) / (2 * sigma**2))
    degree = np.diag(np.sum(affinity, axis=1))
    laplacian = degree - affinity
    _, vectors = np.linalg.eigh(laplacian)
    embedding = vectors[:, : max(1, min(n_clusters, vectors.shape[1]))]
    result = kmeans_cluster(embedding, n_clusters=n_clusters)
    result["method"] = "Spectral"
    return result


def behavior_embeddings(matrix: Sequence[Sequence[float]]) -> dict[str, Any]:
    """Generate PCA, UMAP-compatible, and t-SNE-compatible embeddings."""

    return {
        "PCA": pca_embedding(matrix),
        "UMAP": umap_embedding(matrix),
        "tSNE": tsne_embedding(matrix),
    }


def nearest_neighbors(
    matrix: Sequence[Sequence[float]],
    *,
    query_index: int,
    k: int = 3,
) -> dict[str, Any]:
    """Return nearest neighbors for one sample."""

    values = standardize_features(matrix)
    query = values[int(query_index)]
    distances = np.linalg.norm(values - query, axis=1)
    order = [index for index in np.argsort(distances).tolist() if index != query_index][:k]
    return {
        "query_index": int(query_index),
        "neighbors": [{"index": int(index), "distance": float(distances[index])} for index in order],
    }


def similarity_search(matrix: Sequence[Sequence[float]], *, query_vector: Sequence[float], k: int = 3) -> dict[str, Any]:
    """Search nearest samples to a supplied feature vector."""

    values = standardize_features(matrix)
    query = np.asarray(query_vector, dtype=float).ravel()
    if query.size != values.shape[1]:
        raise ValueError("query_vector length must match feature count.")
    mean = np.mean(_matrix(matrix), axis=0)
    std = np.std(_matrix(matrix), axis=0)
    std[std == 0] = 1.0
    query = (query - mean) / std
    distances = np.linalg.norm(values - query, axis=1)
    order = np.argsort(distances).tolist()[:k]
    return {"neighbors": [{"index": int(index), "distance": float(distances[index])} for index in order]}


def _matrix(values: Sequence[Sequence[float]]) -> np.ndarray:
    matrix = np.asarray(values, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError("feature matrix must have shape (n_samples, n_features).")
    if not np.isfinite(matrix).all():
        raise ValueError("feature matrix must be finite.")
    return matrix


def _distance_matrix(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return np.linalg.norm(left[:, None, :] - right[None, :, :], axis=2)


__all__ = [
    "behavior_embeddings",
    "dbscan_cluster",
    "hierarchical_cluster",
    "kmeans_cluster",
    "nearest_neighbors",
    "pca_embedding",
    "similarity_search",
    "spectral_cluster",
    "standardize_features",
    "tsne_embedding",
    "umap_embedding",
]
