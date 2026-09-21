"""
Anomaly detection package.

Provides a pluggable detector interface and concrete implementations:
- ZScoreDetector: Rolling z-score / EWMA based detection
- IsolationForestDetector: scikit-learn IsolationForest (Phase 2+)

Detector choice is controlled via the ANOMALY_DETECTOR env var.
"""

from app.detection.interface import AnomalyDetector, DetectionResult
from app.detection.factory import get_detector

__all__ = ["AnomalyDetector", "DetectionResult", "get_detector"]
