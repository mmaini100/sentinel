"""
Anomaly detector interface.

All detector implementations must implement the AnomalyDetector protocol.
This allows swapping detectors (z-score, IsolationForest, etc.) via config
without changing any calling code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DetectionResult:
    """Result of anomaly detection on a single event."""

    is_anomalous: bool
    anomaly_score: float  # Higher = more anomalous. Range depends on detector.
    detector_name: str

    def __repr__(self) -> str:
        return (
            f"DetectionResult(anomalous={self.is_anomalous}, "
            f"score={self.anomaly_score:.3f}, detector={self.detector_name})"
        )


class AnomalyDetector(Protocol):
    """
    Protocol for anomaly detectors.

    Each detector maintains per-(service, metric) state and can process
    events one at a time, returning a DetectionResult.
    """

    @property
    def name(self) -> str:
        """Human-readable name of this detector."""
        ...

    def detect(
        self,
        service_name: str,
        metric_name: str,
        value: float,
    ) -> DetectionResult:
        """
        Evaluate a single metric value for anomalies.

        Args:
            service_name: Name of the service emitting the metric.
            metric_name: Name of the metric (e.g. 'request_latency_ms').
            value: The numeric value to evaluate.

        Returns:
            DetectionResult with is_anomalous flag and anomaly_score.
        """
        ...

    def reset(self) -> None:
        """Clear all internal state (useful for testing)."""
        ...
