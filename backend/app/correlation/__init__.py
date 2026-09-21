"""
Correlation engine package.

Groups anomalous events across dependent services into incidents
using the service dependency graph and a configurable time window.
"""

from app.correlation.engine import CorrelationEngine

__all__ = ["CorrelationEngine"]
