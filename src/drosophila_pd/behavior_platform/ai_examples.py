"""Deterministic synthetic datasets for exercising v2 AI pipelines."""

from __future__ import annotations

import numpy as np

from drosophila_pd.behavior_platform.ai_dataset import BehaviorDataset, BehaviorSample


def synthetic_behavior_dataset(
    *,
    dataset_id: str = "synthetic_v2_behavior_examples",
    sample_count: int = 6,
    sample_length: int = 24,
) -> BehaviorDataset:
    """Generate deterministic synthetic rollout-like samples.

    The generated samples are for pipeline validation only and are not
    scientific evidence.
    """

    if sample_count <= 0 or sample_length < 3:
        raise ValueError("sample_count must be positive and sample_length must be at least 3.")
    samples = []
    t = np.linspace(0.0, 1.0, sample_length)
    for index in range(sample_count):
        condition = ("Healthy", "Candidate", "Progression", "Intervention", "Custom")[index % 5]
        scale = 1.0 - 0.05 * index
        x = scale * np.linspace(0.0, 10.0, sample_length)
        y = np.sin(2 * np.pi * t + index * 0.2) * (1.0 + 0.1 * index)
        positions = np.column_stack([x, y, np.ones(sample_length)])
        heading = np.unwrap(np.arctan2(np.gradient(y), np.gradient(x)))
        contact_lf = (np.arange(sample_length) % 4 < 2).astype(float)
        contact_rf = 1.0 - contact_lf
        states = ["Walk" if j % 5 else "Pause" for j in range(sample_length)]
        samples.append(
            BehaviorSample(
                sample_id=f"synthetic_{index:02d}",
                condition=condition,
                arrays={
                    "thorax_positions": positions,
                    "heading": heading,
                    "contact_LF": contact_lf,
                    "contact_RF": contact_rf,
                },
                labels=(condition, "synthetic"),
                metadata={
                    "synthetic": True,
                    "scientific_evidence": False,
                    "timestep_s": 0.05,
                    "state_sequence": states,
                    "gait_summary": {"stability_index": 0.8 + 0.01 * index, "gait_entropy_bits": 1.0},
                },
            )
        )
    return BehaviorDataset(
        dataset_id=dataset_id,
        version="synthetic_v2.1",
        samples=tuple(samples),
        metadata={
            "synthetic": True,
            "scientific_evidence": False,
            "purpose": "deterministic pipeline validation",
        },
    )


__all__ = ["synthetic_behavior_dataset"]
