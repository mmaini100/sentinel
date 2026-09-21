"""
Z-Score / EWMA anomaly detector.

Maintains a rolling window of values per (service, metric) pair and flags
values whose deviation from the EWMA baseline exceeds a configurable
threshold in terms of standard deviations.

The key insight: we use a slow-moving EWMA (small alpha) as the baseline,
so sudden spikes are detected even if the raw window gets contaminated
with spike values. The standard deviation is computed from the window
but the comparison is against the EWMA baseline.

Configurable via:
  - ANOMALY_ZSCORE_WINDOW: Number of observations in the rolling window (default 30)
  - ANOMALY_ZSCORE_THRESHOLD: Z-score threshold to flag as anomalous (default 3.0)
"""

from __future__ import annotations

import logging
import math
from collections import defaultdict, deque

from app.detection.interface import AnomalyDetector, DetectionResult

logger = logging.getLogger("sentinel.detection.zscore")


class ZScoreDetector:
    """
    Rolling z-score anomaly detector with EWMA baseline.

    For each (service, metric) pair, maintains:
    - A sliding window of recent values for std computation
    - A slow EWMA as the stable baseline (resists spike contamination)

    A value is flagged anomalous if its distance from the EWMA baseline,
    measured in units of the rolling standard deviation, exceeds the threshold.

    The slow EWMA (alpha = 0.05) adapts very gradually, so a sudden 10x spike
    still registers as anomalous even after several spike observations enter
    the window.
    """

    def __init__(
        self,
        window_size: int = 30,
        threshold: float = 3.0,
    ) -> None:
        self._window_size = window_size
        self._threshold = threshold
        # {(service, metric): deque of recent values}
        self._windows: dict[tuple[str, str], deque[float]] = defaultdict(
            lambda: deque(maxlen=window_size)
        )
        # Slow EWMA for stable baseline (resists spike contamination)
        self._ewma: dict[tuple[str, str], float] = {}
        self._ewma_alpha = 0.05  # Very slow — takes ~20 obs to shift significantly
        # Also track a fast std estimate for comparison
        self._baseline_std: dict[tuple[str, str], float] = {}
        self._observation_count: dict[tuple[str, str], int] = defaultdict(int)

    @property
    def name(self) -> str:
        return "zscore"

    def detect(
        self,
        service_name: str,
        metric_name: str,
        value: float,
    ) -> DetectionResult:
        """
        Evaluate a metric value against the EWMA baseline.

        Returns DetectionResult with:
          - is_anomalous: True if deviation from EWMA > threshold * baseline_std
          - anomaly_score: normalized deviation score
        """
        key = (service_name, metric_name)
        window = self._windows[key]
        self._observation_count[key] += 1
        count = self._observation_count[key]

        # Update EWMA baseline
        if key in self._ewma:
            # Only update EWMA from non-anomalous values to prevent baseline corruption
            # On first pass, always update
            old_ewma = self._ewma[key]
            # Tentatively update
            new_ewma = self._ewma_alpha * value + (1 - self._ewma_alpha) * old_ewma
        else:
            self._ewma[key] = value
            new_ewma = value
            old_ewma = value

        # Add to window
        window.append(value)

        # Need at least 5 samples for meaningful stats
        min_samples = 5
        if count < min_samples:
            self._ewma[key] = new_ewma
            return DetectionResult(
                is_anomalous=False,
                anomaly_score=0.0,
                detector_name=self.name,
            )

        # Compute std from the window
        mean = sum(window) / len(window)
        variance = sum((x - mean) ** 2 for x in window) / len(window)
        std = math.sqrt(variance) if variance > 0 else 0.0

        # Also maintain a baseline std that only updates slowly
        if key not in self._baseline_std or self._baseline_std[key] < 1e-10:
            self._baseline_std[key] = std
        else:
            # Slow update of baseline std
            self._baseline_std[key] = (
                0.05 * std + 0.95 * self._baseline_std[key]
            )

        # Use the smaller of current std and baseline std for comparison
        # This prevents the std from inflating during a spike, which would
        # mask the anomaly
        effective_std = min(std, self._baseline_std[key]) if self._baseline_std[key] > 1e-10 else std

        if effective_std < 1e-10:
            self._ewma[key] = new_ewma
            return DetectionResult(
                is_anomalous=False,
                anomaly_score=0.0,
                detector_name=self.name,
            )

        # Z-score: distance from EWMA baseline in units of effective std
        # We only care about positive spikes (latency up, errors up)
        z_score = (value - old_ewma) / effective_std
        is_anomalous = z_score > self._threshold

        # Only update EWMA if not anomalous (protect the baseline)
        if not is_anomalous:
            self._ewma[key] = new_ewma
        # If anomalous, keep the old EWMA to maintain a clean baseline

        if is_anomalous:
            logger.info(
                f"Anomaly detected: {service_name}/{metric_name} "
                f"value={value:.2f} z_score={z_score:.2f} "
                f"ewma={old_ewma:.2f} eff_std={effective_std:.2f}"
            )

        return DetectionResult(
            is_anomalous=is_anomalous,
            anomaly_score=round(z_score, 4),
            detector_name=self.name,
        )

    def reset(self) -> None:
        """Clear all internal state."""
        self._windows.clear()
        self._ewma.clear()
        self._baseline_std.clear()
        self._observation_count.clear()
