from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.behavior_platform import (  # noqa: E402
    ARTIFACT_CATEGORIES,
    CAMPAIGN_SCOPE,
    CampaignArtifactManager,
    CampaignCheckpoint,
    CampaignConfig,
    CampaignDatasetBuilder,
    CampaignFigureFactory,
    CampaignRunner,
    CampaignScheduler,
    artifact_manifest_from_paths,
    collect_campaign_provenance,
    create_campaign,
    deterministic_artifact_layout,
    directory_manifest,
    file_sha256,
    generate_experiment_matrix,
    generate_paper_assets,
    load_campaign_config,
    load_campaign_results,
    merge_campaign_datasets,
    replay_campaign_plan,
    resume_campaign,
    save_campaign,
    stable_hash,
    synthetic_behavior_dataset,
    validate_campaign_dataset,
    verify_artifact_hashes,
    verify_campaign_replay,
    verify_dataset_package,
    verify_manifest_signature,
    write_provenance_manifest,
)


def test_campaign_matrix_manifest_resume_and_validation_errors(tmp_path):
    config = CampaignConfig(
        campaign_id="campaign_a",
        roles=("Healthy", "Candidate"),
        progression_stages=("Stage0",),
        interventions=("none",),
        custom_scenarios=("open_field",),
        parameter_grid={"motor_scale": (1.0, 0.8), "coupling_scale": (1.0,)},
        seeds=(0, 1),
        replicates=2,
    )
    plans = generate_experiment_matrix(config)
    assert len(plans) == 16
    assert len({plan.experiment_id for plan in plans}) == 16
    assert plans == CampaignScheduler().schedule(config)
    assert plans[0].metadata["scientific_scope"] == CAMPAIGN_SCOPE

    campaign = create_campaign(config)
    assert campaign.manifest.experiment_count == 16
    assert campaign.manifest.config_hash == stable_hash(config.as_dict())
    saved = save_campaign(campaign, tmp_path / "campaign.json")
    assert json.loads(saved.read_text(encoding="utf-8"))["manifest"]["experiment_count"] == 16

    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config.as_dict()), encoding="utf-8")
    assert load_campaign_config(config_path).campaign_id == "campaign_a"

    checkpoint = CampaignCheckpoint(campaign_id="campaign_a", completed_ids=(plans[0].experiment_id,))
    resume = resume_campaign(campaign, checkpoint)
    assert len(resume.remaining) == 15
    assert plans[0] not in resume.remaining
    assert checkpoint.as_dict()["checkpoint_hash"]

    with pytest.raises(ValueError, match="campaign_id"):
        CampaignConfig(campaign_id="")
    with pytest.raises(ValueError, match="replicates"):
        CampaignConfig(campaign_id="bad", replicates=0)
    with pytest.raises(ValueError, match="seed"):
        CampaignConfig(campaign_id="bad", seeds=())


def test_campaign_runner_checkpoint_outputs_and_failure_path(tmp_path):
    config = CampaignConfig(campaign_id="runner", roles=("Healthy",), seeds=(0, 1), replicates=1)
    campaign = create_campaign(config)

    def executor(plan):
        if plan.seed == 1:
            raise RuntimeError("planned failure")
        return {"experiment": plan.as_dict(), "condition": plan.role, "metrics": {"mean_speed": 1.0}}

    history, checkpoint = CampaignRunner().run(campaign, executor, output_dir=tmp_path)
    assert len(history.events) == 2
    assert len(checkpoint.completed_ids) == 1
    assert len(checkpoint.failed_ids) == 1
    assert (tmp_path / "campaign_checkpoint.json").exists()
    assert (tmp_path / "campaign_manifest.json").exists()
    assert (tmp_path / "logs" / "campaign_log.jsonl").exists()

    resumed_history, resumed_checkpoint = CampaignRunner().run(
        campaign,
        lambda plan: {"experiment": plan.as_dict(), "metrics": {"mean_speed": 2.0}},
        checkpoint=checkpoint,
        output_dir=tmp_path,
    )
    assert len(resumed_history.events) == 0
    assert resumed_checkpoint.failed_ids == checkpoint.failed_ids


def test_campaign_dataset_package_merge_and_validation(tmp_path):
    results = [
        {
            "experiment": {"experiment_id": "exp_a", "role": "Healthy", "seed": 0, "replicate": 0},
            "arrays": {"thorax_positions": np.zeros((3, 3)).tolist()},
            "metrics": {"mean_speed": 1.0},
        },
        {
            "experiment": {"experiment_id": "exp_b", "role": "Candidate", "seed": 1, "replicate": 0},
            "metrics": {"mean_speed": 0.8, "yaw_rate_abs_mean": 0.1},
        },
    ]
    builder = CampaignDatasetBuilder("campaign_dataset")
    dataset = builder.build(results)
    assert len(dataset.samples) == 2
    assert dataset.samples[1].arrays["metrics_vector"]
    validation = validate_campaign_dataset(dataset)
    assert validation["overall_pass"] is True

    files = builder.export_package(results, tmp_path / "dataset")
    assert {"dataset_json", "dataset_csv", "dataset_npz", "manifest", "index"} == set(files)
    loaded_results = load_campaign_results([files["dataset_json"]])
    assert loaded_results[0]["dataset_id"] == "campaign_dataset"
    verify = verify_dataset_package(files["dataset_json"], files["manifest"])
    assert verify["overall_pass"] is True

    merged = merge_campaign_datasets([dataset, synthetic_behavior_dataset(sample_count=1)], dataset_id="merged")
    assert len(merged.samples) == 3
    with pytest.raises(ValueError, match="duplicate"):
        merge_campaign_datasets([dataset, dataset], dataset_id="bad")


def test_artifact_manager_figures_paper_assets_and_hash_verification(tmp_path):
    layout = deterministic_artifact_layout(tmp_path, "campaign_x")
    assert set(layout) == set(ARTIFACT_CATEGORIES)
    source = tmp_path / "source.json"
    source.write_text('{"ok": true}', encoding="utf-8")
    manager = CampaignArtifactManager(tmp_path / "campaign_x")
    artifact = manager.register_file(source, "json")
    assert artifact.sha256 == file_sha256(artifact.path)
    manifest_path = manager.write_manifest()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["artifacts"]
    assert verify_artifact_hashes(manifest)["overall_pass"] is True
    assert artifact_manifest_from_paths([artifact.path])[artifact.path.as_posix()]["sha256"] == artifact.sha256
    assert directory_manifest(tmp_path / "campaign_x")

    reports = [
        {
            "condition": "Healthy",
            "arrays": {"thorax_positions": [[0, 0, 0], [1, 0.1, 0], [2, 0, 0]]},
            "metrics": {
                "mean_speed": 1.0,
                "yaw_rate_abs_mean": 0.1,
                "gait_score": 0.8,
                "exploration_index": 0.6,
                "comparison_score": 1.0,
                "benchmark_score": 0.9,
                "progression_stage_index": 0,
            },
        }
    ]
    figure_files = CampaignFigureFactory(tmp_path / "figures").generate_all(reports, formats=("png", "svg"))
    assert "trajectory_png" in figure_files
    assert all(path.exists() and path.stat().st_size > 0 for path in figure_files.values())
    with pytest.raises(ValueError, match="unsupported"):
        CampaignFigureFactory(tmp_path / "bad").generate_all(reports, formats=("bmp",))

    table = tmp_path / "table.csv"
    stats = tmp_path / "stats.json"
    table.write_text("a,b\n1,2\n", encoding="utf-8")
    stats.write_text('{"n": 1}', encoding="utf-8")
    paper = generate_paper_assets(
        figure_files={"trajectory": figure_files["trajectory_png"]},
        table_files={"summary": table},
        statistics_files={"stats": stats},
        output_dir=tmp_path / "paper",
    )
    assert paper["manifest"].exists()
    assert (tmp_path / "paper" / "paper_figures").exists()


def test_provenance_replay_manifest_signature_and_artifact_failures(tmp_path):
    config = CampaignConfig(campaign_id="prov", roles=("Healthy",), seeds=(0,))
    campaign = create_campaign(config)
    artifact = tmp_path / "artifact.json"
    artifact.write_text("{}", encoding="utf-8")
    provenance = collect_campaign_provenance(
        campaign_id="prov",
        config=config.as_dict(),
        artifacts=(artifact,),
        seeds=config.seeds,
        dataset_path=artifact,
    )
    path = write_provenance_manifest(provenance, tmp_path / "provenance.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["configuration_hash"] == stable_hash(config.as_dict())
    assert payload["dataset_hash"] == file_sha256(artifact)
    assert payload["software_versions"]["python"]

    replay = replay_campaign_plan(config)
    assert replay["experiment_ids"] == list(campaign.manifest.experiment_ids)
    assert verify_campaign_replay(config, campaign.manifest.as_dict())["overall_pass"] is True
    assert verify_manifest_signature(campaign.manifest.as_dict())["overall_pass"] is True
    assert verify_manifest_signature(campaign.manifest.as_dict(), expected_hash="bad")["overall_pass"] is False
    bad = {"artifacts": [{"path": (tmp_path / "missing.json").as_posix(), "sha256": "x"}]}
    assert verify_artifact_hashes(bad)["overall_pass"] is False


def test_research_campaign_cli_end_to_end(tmp_path):
    config_path = tmp_path / "config.json"
    config = CampaignConfig(campaign_id="cli", roles=("Healthy", "Candidate"), seeds=(0,), parameter_grid={"motor": (1.0,)})
    config_path.write_text(json.dumps(config.as_dict()), encoding="utf-8")
    script = REPO_ROOT / "scripts" / "research_campaign_cli.py"

    plan_path = tmp_path / "plan.json"
    create = subprocess.run(
        [sys.executable, str(script), "create", "--config", str(config_path), "--output", str(plan_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(create.stdout)["overall_pass"] is True
    assert plan_path.exists()

    execute_dir = tmp_path / "execute"
    execute = subprocess.run(
        [sys.executable, str(script), "execute", "--config", str(config_path), "--output-dir", str(execute_dir)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(execute.stdout)["completed"] == 2

    reports = sorted((execute_dir / "reports").glob("*.json"))
    dataset = subprocess.run(
        [
            sys.executable,
            str(script),
            "dataset",
            "--input",
            *(str(path) for path in reports),
            "--output-dir",
            str(tmp_path / "dataset"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(dataset.stdout)["overall_pass"] is True

    for command in ("artifacts", "figures", "report"):
        result = subprocess.run(
            [sys.executable, str(script), command, "--output-dir", str(tmp_path / command)],
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(result.stdout)["overall_pass"] is True

    manifest = execute_dir / "provenance_manifest.json"
    verify = subprocess.run(
        [sys.executable, str(script), "verify", "--manifest", str(manifest)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(verify.stdout)["overall_pass"] is True
