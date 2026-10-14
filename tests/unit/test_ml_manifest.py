"""
Unit tests for INTELLICLUSTER ML artifact manifest and integrity verification.
"""

from pathlib import Path
import pytest

from intellicluster.ml.manifest import (
    EXPECTED_ARTIFACTS,
    ExpectedArtifact,
    _validate_safe_artifact_path,
    compute_file_sha256,
    format_cli_summary,
    get_default_models_dir,
    verify_artifact_manifest,
)


def test_baseline_manifest_verifies_all_ten_artifacts():
    """Verify that the repository's ml_models directory passes full baseline manifest verification."""
    report = verify_artifact_manifest()
    assert report.is_valid is True
    assert report.total_expected == 10
    assert report.total_verified == 10
    assert report.total_missing == 0
    assert report.total_mismatched == 0

    # Ensure all items status is VERIFIED
    for item in report.items:
        assert item.status == "VERIFIED"
        assert item.actual_sha256 == item.expected_sha256
        assert item.actual_size_bytes == item.expected_size_bytes


def test_compute_file_sha256(tmp_path: Path):
    """Test SHA-256 calculation on controlled file content."""
    sample_file = tmp_path / "sample.txt"
    sample_file.write_text("hello intellicluster", encoding="utf-8")

    # Echo "hello intellicluster" sha256
    expected_hash = "1c3b5e086a9cf3bdc6e75e8076036beb2e23468734e32332974c23453d330737"
    assert compute_file_sha256(sample_file) == expected_hash


def test_missing_artifact_reporting(tmp_path: Path):
    """Test that missing artifact is accurately identified and report marked invalid."""
    fake_specs = {
        "missing_model.joblib": ExpectedArtifact(
            filename="missing_model.joblib",
            model_id="test-model",
            artifact_type="primary_model",
            companion_of=None,
            algorithm="Test",
            expected_sha256="deadbeef" * 8,
            expected_size_bytes=100,
            operational_status="READY",
            source_dataset="data/test.csv",
            notes="Test missing",
        )
    }

    report = verify_artifact_manifest(models_dir=tmp_path, expected_specs=fake_specs)
    assert report.is_valid is False
    assert report.total_missing == 1
    assert report.total_verified == 0
    assert report.items[0].status == "MISSING"
    assert "File not found" in report.items[0].details


def test_mismatched_checksum_reporting(tmp_path: Path):
    """Test that corrupted or mismatched artifact checksum is caught."""
    corrupted_file = tmp_path / "corrupted_model.joblib"
    corrupted_file.write_bytes(b"tampered model payload")

    fake_specs = {
        "corrupted_model.joblib": ExpectedArtifact(
            filename="corrupted_model.joblib",
            model_id="test-model",
            artifact_type="primary_model",
            companion_of=None,
            algorithm="Test",
            expected_sha256="0000000000000000000000000000000000000000000000000000000000000000",
            expected_size_bytes=len(b"tampered model payload"),
            operational_status="READY",
            source_dataset="data/test.csv",
            notes="Test checksum mismatch",
        )
    }

    report = verify_artifact_manifest(models_dir=tmp_path, expected_specs=fake_specs)
    assert report.is_valid is False
    assert report.total_mismatched == 1
    assert report.items[0].status == "HASH_MISMATCH"
    assert "SHA-256 mismatch" in report.items[0].details


def test_mismatched_size_reporting(tmp_path: Path):
    """Test that size mismatch with otherwise dummy hash is caught."""
    sample_file = tmp_path / "size_mismatch.joblib"
    payload = b"test payload"
    sample_file.write_bytes(payload)

    actual_hash = compute_file_sha256(sample_file)

    fake_specs = {
        "size_mismatch.joblib": ExpectedArtifact(
            filename="size_mismatch.joblib",
            model_id="test-model",
            artifact_type="primary_model",
            companion_of=None,
            algorithm="Test",
            expected_sha256=actual_hash,
            expected_size_bytes=len(payload) + 50,  # wrong size
            operational_status="READY",
            source_dataset="data/test.csv",
            notes="Test size mismatch",
        )
    }

    report = verify_artifact_manifest(models_dir=tmp_path, expected_specs=fake_specs)
    assert report.is_valid is False
    assert report.total_mismatched == 1
    assert report.items[0].status == "SIZE_MISMATCH"
    assert "Size mismatch" in report.items[0].details


def test_path_traversal_rejection(tmp_path: Path):
    """Ensure directory traversal attacks are rejected by safe path resolver."""
    with pytest.raises(ValueError, match="Path traversal or nested directory not permitted"):
        _validate_safe_artifact_path(tmp_path, "../outside.joblib")

    with pytest.raises(ValueError, match="Path traversal or nested directory not permitted"):
        _validate_safe_artifact_path(tmp_path, "subfolder/nested.joblib")


def test_relative_path_resolution_independent_of_cwd(monkeypatch, tmp_path: Path):
    """Ensure get_default_models_dir correctly resolves regardless of current working directory."""
    monkeypatch.chdir(tmp_path)
    models_dir = get_default_models_dir()
    assert models_dir.is_absolute()
    assert models_dir.name == "ml_models"
    assert models_dir.exists()


def test_non_destructive_verification():
    """Verify that manifest verification preserves artifact mtimes and file contents."""
    models_dir = get_default_models_dir()
    test_artifact = models_dir / "server_clustering_scaler.joblib"
    mtime_before = test_artifact.stat().st_mtime_ns
    bytes_before = test_artifact.read_bytes()

    report = verify_artifact_manifest()
    assert report.is_valid is True

    mtime_after = test_artifact.stat().st_mtime_ns
    bytes_after = test_artifact.read_bytes()

    assert mtime_before == mtime_after
    assert bytes_before == bytes_after


def test_cli_summary_formatting():
    """Verify summary string representation."""
    report = verify_artifact_manifest()
    summary = format_cli_summary(report)
    assert "[PASSED] All artifacts intact" in summary
    assert "10/10 verified" in summary
    assert "server_clustering_kmeans.joblib" in summary
