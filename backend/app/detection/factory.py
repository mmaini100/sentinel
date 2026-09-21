"""
Detector factory — instantiates the correct anomaly detector
based on the ANOMALY_DETECTOR environment variable.
"""

from __future__ import annotations

import logging

from app.config import settings
from app.detection.interface import AnomalyDetector
from app.detection.zscore import ZScoreDetector

logger = logging.getLogger("sentinel.detection.factory")


def get_detector() -> AnomalyDetector:
    """
    Create and return an anomaly detector instance based on config.

    Raises ValueError if the configured detector type is unknown.
    """
    detector_type = settings.ANOMALY_DETECTOR.lower()

    if detector_type == "zscore":
        detector = ZScoreDetector(
            window_size=settings.ANOMALY_ZSCORE_WINDOW,
            threshold=settings.ANOMALY_ZSCORE_THRESHOLD,
        )
        logger.info(
            f"Initialized ZScoreDetector "
            f"(window={settings.ANOMALY_ZSCORE_WINDOW}, "
            f"threshold={settings.ANOMALY_ZSCORE_THRESHOLD})"
        )
        return detector

    elif detector_type == "isolation_forest":
        # Placeholder for Phase 2+ IsolationForest implementation
        raise NotImplementedError(
            "IsolationForest detector not yet implemented. "
            "Use ANOMALY_DETECTOR=zscore for now."
        )

    else:
        raise ValueError(
            f"Unknown anomaly detector type: {detector_type!r}. "
            f"Valid options: 'zscore', 'isolation_forest'"
        )
