"""
Machine Learning Artifact Manifest and Integrity Verification for INTELLICLUSTER.

Inventories expected runtime model artifacts, calculates SHA-256 checksums,
detects missing or corrupted files, identifies companion scalers/metadata,
and maps repository training dataset provenance without loading model objects.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import logging
from pathlib import Path
import sys
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExpectedArtifact:
    """Specification for an expected trained ML model artifact or companion file."""

    filename: str
    model_id: str
    artifact_type: str  # "primary_model" or "companion"
    companion_of: Optional[str]
    algorithm: str
    expected_sha256: str
    expected_size_bytes: int
    operational_status: str  # "READY", "REJECTED", "EXPERIMENTAL"
    source_dataset: Optional[str]
    notes: str


# Verified baseline inventory of the 10 pre-trained artifacts in ml_models/
EXPECTED_ARTIFACTS: dict[str, ExpectedArtifact] = {
    "server_clustering_kmeans.joblib": ExpectedArtifact(
        filename="server_clustering_kmeans.joblib",
        model_id="model-1",
        artifact_type="primary_model",
        companion_of=None,
        algorithm="K-Means (k=4)",
        expected_sha256="242bc682c0e3467ec7420cc1c3646c9f218bfc36213d66fe763cd86f43b0eefc",
        expected_size_bytes=49922,
        operational_status="READY",
        source_dataset="data/Midterm_53_group.csv",
        notes="Cluster centroids and archetype profiles for compute node archetyping.",
    ),
    "server_clustering_scaler.joblib": ExpectedArtifact(
        filename="server_clustering_scaler.joblib",
        model_id="model-1",
        artifact_type="companion",
        companion_of="server_clustering_kmeans.joblib",
        algorithm="StandardScaler",
        expected_sha256="c2b8e7c0e03f1d085163ec41e718e3a63bbe76b0914e7fb86d95ff5d7b2020c4",
        expected_size_bytes=3460,
        operational_status="READY",
        source_dataset="data/Midterm_53_group.csv",
        notes="StandardScaler preprocessor required for Model 1 feature normalization.",
    ),
    "failure_prediction_ai4i_xgboost.joblib": ExpectedArtifact(
        filename="failure_prediction_ai4i_xgboost.joblib",
        model_id="model-2a",
        artifact_type="primary_model",
        companion_of=None,
        algorithm="XGBoost Classifier (Stratified 5-Fold)",
        expected_sha256="42037548f01b6616501dcf80d29617cf5c66135ed8734424fcb5360117637fab",
        expected_size_bytes=252502,
        operational_status="READY",
        source_dataset="data/ai4i2020.csv",
        notes="Hardware failure risk predictor trained on AI4I industrial machine sensors.",
    ),
    "failure_prediction_environmental_xgboost.joblib": ExpectedArtifact(
        filename="failure_prediction_environmental_xgboost.joblib",
        model_id="model-2b",
        artifact_type="primary_model",
        companion_of=None,
        algorithm="XGBoost Classifier (Stratified 5-Fold)",
        expected_sha256="750790c38e013dfe50a092bf5780848d4f7cc46cece243d1d0297a7e01f9270e",
        expected_size_bytes=234867,
        operational_status="REJECTED",
        source_dataset="data/machine_failure_data.csv",
        notes="Quarantined model. Disqualified due to synthetic noise overfitting (OOF ROC-AUC=0.4891).",
    ),
    "resource_forecasting_lstm.pt": ExpectedArtifact(
        filename="resource_forecasting_lstm.pt",
        model_id="model-3",
        artifact_type="primary_model",
        companion_of=None,
        algorithm="Dual-Layer Stacked LSTM",
        expected_sha256="1cc5dc07ebfd18da4ac96324a6b952e12faae47be6669448effac2136840a43f",
        expected_size_bytes=136805,
        operational_status="READY",
        source_dataset="data/Workload_Dataset.csv / predicting-service-request-loads.ipynb",
        notes="PyTorch state dict forecasting [cpu_utilization, memory_usage, workload] over 24h.",
    ),
    "resource_forecasting_metadata.joblib": ExpectedArtifact(
        filename="resource_forecasting_metadata.joblib",
        model_id="model-3",
        artifact_type="companion",
        companion_of="resource_forecasting_lstm.pt",
        algorithm="Metadata & Scaler Bundle",
        expected_sha256="23e57118897b3bbb199daa7b19d9a0ddd1116f3ebca1b1273cb24f4d72dfded9",
        expected_size_bytes=2006,
        operational_status="READY",
        source_dataset="data/Workload_Dataset.csv / predicting-service-request-loads.ipynb",
        notes="Contains MinMaxScaler, architecture params, input features (5), and target features (3).",
    ),
    "network_anomaly_iforest.joblib": ExpectedArtifact(
        filename="network_anomaly_iforest.joblib",
        model_id="model-4a",
        artifact_type="primary_model",
        companion_of=None,
        algorithm="Isolation Forest",
        expected_sha256="8f39d4837bf782189d9fd7e77fd1fcb7a6bebf239a3d67856e6ebbc712e3f80f",
        expected_size_bytes=3407650,
        operational_status="REJECTED",
        source_dataset="data/embedded_system_network_security_dataset.csv",
        notes="Quarantined model. Disqualified due to normal vs attack score parity (ROC-AUC=0.4980).",
    ),
    "infrastructure_anomaly_iforest.joblib": ExpectedArtifact(
        filename="infrastructure_anomaly_iforest.joblib",
        model_id="model-4b",
        artifact_type="primary_model",
        companion_of=None,
        algorithm="Isolation Forest (Contamination=5%)",
        expected_sha256="5449c1890324ae96bec41d8d9f7e13c653024a5742798fbee28754c6095ba62b",
        expected_size_bytes=1849378,
        operational_status="READY",
        source_dataset="data/cloud_ecommerce_performance_tradeoff_dataset.csv",
        notes="Contextual multivariate outlier scoring for infrastructure host telemetry.",
    ),
    "load_balancer_dqn.pt": ExpectedArtifact(
        filename="load_balancer_dqn.pt",
        model_id="model-5",
        artifact_type="primary_model",
        companion_of=None,
        algorithm="Deep Q-Network (DQN)",
        expected_sha256="af6040fc7f40dbd3d45b1c20c44cdbb29b7b23f3af8dc6ed92e602c0d6c2b8f4",
        expected_size_bytes=50573,
        operational_status="EXPERIMENTAL",
        source_dataset="data/Load Balancing Improved.csv",
        notes="Experimental RL placement weights. Read-only advisory, not active scheduler.",
    ),
    "load_balancer_metadata.joblib": ExpectedArtifact(
        filename="load_balancer_metadata.joblib",
        model_id="model-5",
        artifact_type="companion",
        companion_of="load_balancer_dqn.pt",
        algorithm="Metadata Bundle",
        expected_sha256="580406c6e36da78db62d59ee5149aeee52c58a5d2b0f4ada8ef601345b190c7d",
        expected_size_bytes=1100,
        operational_status="EXPERIMENTAL",
        source_dataset="data/Load Balancing Improved.csv",
        notes="Contains state_dim (25), action_dim (4), and node archetypes for DQN state encoding.",
    ),
}


@dataclass
class ArtifactVerificationItem:
    """Result of verifying an individual artifact file."""

    filename: str
    model_id: str
    artifact_type: str
    operational_status: str
    status: str  # "VERIFIED", "MISSING", "HASH_MISMATCH", "SIZE_MISMATCH", "ERROR"
    expected_sha256: str
    actual_sha256: Optional[str]
    expected_size_bytes: int
    actual_size_bytes: Optional[int]
    source_dataset: Optional[str]
    details: str


@dataclass
class ManifestReport:
    """Consolidated manifest verification report."""

    verified_at: str
    models_dir: str
    total_expected: int
    total_verified: int
    total_missing: int
    total_mismatched: int
    is_valid: bool
    items: list[ArtifactVerificationItem]

    def to_dict(self) -> dict:
        """Convert report to dictionary format."""
        return asdict(self)


def get_default_models_dir() -> Path:
    """Return trusted repository-relative models directory."""
    return Path(__file__).resolve().parents[2] / "ml_models"


def compute_file_sha256(file_path: Path, chunk_size: int = 65536) -> str:
    """
    Compute SHA-256 checksum of a file by streaming binary chunks.
    Does not load or deserialize model objects.
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def _validate_safe_artifact_path(base_dir: Path, filename: str) -> Path:
    """
    Resolve and validate that an artifact filename is confined strictly
    within base_dir. Rejects path traversal and nested directories.
    """
    base_resolved = base_dir.resolve()
    target_path = (base_dir / filename).resolve()

    # Reject traversal or subdirectories
    if target_path.parent != base_resolved:
        raise ValueError(f"Path traversal or nested directory not permitted: {filename}")

    return target_path


def verify_artifact_manifest(
    models_dir: Optional[Path] = None,
    expected_specs: Optional[dict[str, ExpectedArtifact]] = None,
) -> ManifestReport:
    """
    Verify integrity of all expected ML runtime artifacts against baseline manifest.

    Non-destructive: strictly reads file bytes and checks checksums/sizes.
    Never modifies, copies, deletes, or retrains any file.
    """
    resolved_dir = (models_dir or get_default_models_dir()).resolve()
    specs = expected_specs or EXPECTED_ARTIFACTS

    items: list[ArtifactVerificationItem] = []
    total_verified = 0
    total_missing = 0
    total_mismatched = 0

    for filename, spec in specs.items():
        try:
            target_path = _validate_safe_artifact_path(resolved_dir, filename)
        except ValueError as ve:
            items.append(
                ArtifactVerificationItem(
                    filename=filename,
                    model_id=spec.model_id,
                    artifact_type=spec.artifact_type,
                    operational_status=spec.operational_status,
                    status="ERROR",
                    expected_sha256=spec.expected_sha256,
                    actual_sha256=None,
                    expected_size_bytes=spec.expected_size_bytes,
                    actual_size_bytes=None,
                    source_dataset=spec.source_dataset,
                    details=str(ve),
                )
            )
            total_mismatched += 1
            continue

        if not target_path.is_file():
            items.append(
                ArtifactVerificationItem(
                    filename=filename,
                    model_id=spec.model_id,
                    artifact_type=spec.artifact_type,
                    operational_status=spec.operational_status,
                    status="MISSING",
                    expected_sha256=spec.expected_sha256,
                    actual_sha256=None,
                    expected_size_bytes=spec.expected_size_bytes,
                    actual_size_bytes=None,
                    source_dataset=spec.source_dataset,
                    details=f"File not found: {target_path}",
                )
            )
            total_missing += 1
            continue

        actual_size = target_path.stat().st_size
        actual_sha256 = compute_file_sha256(target_path)

        if actual_sha256.lower() != spec.expected_sha256.lower():
            items.append(
                ArtifactVerificationItem(
                    filename=filename,
                    model_id=spec.model_id,
                    artifact_type=spec.artifact_type,
                    operational_status=spec.operational_status,
                    status="HASH_MISMATCH",
                    expected_sha256=spec.expected_sha256,
                    actual_sha256=actual_sha256,
                    expected_size_bytes=spec.expected_size_bytes,
                    actual_size_bytes=actual_size,
                    source_dataset=spec.source_dataset,
                    details=f"SHA-256 mismatch. Expected {spec.expected_sha256[:12]}..., got {actual_sha256[:12]}...",
                )
            )
            total_mismatched += 1
        elif actual_size != spec.expected_size_bytes:
            items.append(
                ArtifactVerificationItem(
                    filename=filename,
                    model_id=spec.model_id,
                    artifact_type=spec.artifact_type,
                    operational_status=spec.operational_status,
                    status="SIZE_MISMATCH",
                    expected_sha256=spec.expected_sha256,
                    actual_sha256=actual_sha256,
                    expected_size_bytes=spec.expected_size_bytes,
                    actual_size_bytes=actual_size,
                    source_dataset=spec.source_dataset,
                    details=f"Size mismatch. Expected {spec.expected_size_bytes}B, got {actual_size}B",
                )
            )
            total_mismatched += 1
        else:
            items.append(
                ArtifactVerificationItem(
                    filename=filename,
                    model_id=spec.model_id,
                    artifact_type=spec.artifact_type,
                    operational_status=spec.operational_status,
                    status="VERIFIED",
                    expected_sha256=spec.expected_sha256,
                    actual_sha256=actual_sha256,
                    expected_size_bytes=spec.expected_size_bytes,
                    actual_size_bytes=actual_size,
                    source_dataset=spec.source_dataset,
                    details="Checksum and file size verified against manifest.",
                )
            )
            total_verified += 1

    is_valid = (total_missing == 0) and (total_mismatched == 0)

    return ManifestReport(
        verified_at=datetime.now(timezone.utc).isoformat(),
        models_dir=str(resolved_dir),
        total_expected=len(specs),
        total_verified=total_verified,
        total_missing=total_missing,
        total_mismatched=total_mismatched,
        is_valid=is_valid,
        items=items,
    )


def format_cli_summary(report: ManifestReport) -> str:
    """Format manifest verification report for console output."""
    lines = [
        "=" * 80,
        "INTELLICLUSTER — ML Artifact Integrity & Manifest Report",
        "=" * 80,
        f"Verified At: {report.verified_at}",
        f"Artifacts Directory: {report.models_dir}",
        f"Status: {'[PASSED] All artifacts intact' if report.is_valid else '[FAILED] Integrity check issues detected'}",
        f"Summary: {report.total_verified}/{report.total_expected} verified, "
        f"{report.total_missing} missing, {report.total_mismatched} mismatched",
        "-" * 80,
        f"{'Filename':<46} {'Status':<14} {'Bytes':<10} {'Model ID':<10}",
        "-" * 80,
    ]

    for item in report.items:
        size_str = str(item.actual_size_bytes) if item.actual_size_bytes is not None else "-"
        lines.append(f"{item.filename:<46} {item.status:<14} {size_str:<10} {item.model_id:<10}")

    lines.append("=" * 80)
    return "\n".join(lines)


def main() -> int:
    """Read-only CLI entry point for artifact manifest verification."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Verify integrity and provenance of INTELLICLUSTER ML model artifacts."
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=None,
        help="Path to ml_models directory (defaults to repository ml_models/)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full report in JSON format",
    )
    args = parser.parse_args()

    report = verify_artifact_manifest(models_dir=args.models_dir)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_cli_summary(report))

    return 0 if report.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
