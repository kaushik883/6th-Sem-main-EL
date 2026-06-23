"""
ei_forensics.py
===============
E&I (Electronics & Instrumentation) Forensic Engine for LogiSight.

Analyses JSONB telemetry_data stored on the quotes table to detect:
  1. TELEMETRY_WEIGHT_DROP  – Moving-average based cargo theft detection.
  2. SLA_TEMP_BREACH        – Consecutive-hour temperature exceedance detection.

Usage (standalone):
    from app.services.ei_forensics import TelemetryForensics
    engine = TelemetryForensics()
    anomalies = engine.analyze(telemetry_data, temp_threshold_c=5.0)
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
TelemetryRecord = dict[str, Any]   # Single hourly reading
AnomalyDict     = dict[str, Any]   # Output anomaly payload


# ---------------------------------------------------------------------------
# Main forensics class
# ---------------------------------------------------------------------------

class TelemetryForensics:
    """
    Stateless forensic engine.  Each public method accepts a list of hourly
    sensor dicts and returns a list of anomaly dicts (empty if no issues found).

    Expected record format (produced by generate_telemetry.py):
        {
            "timestamp": "2024-01-15T08:00:00Z",
            "weight_kg": 498.73,
            "temp_c":    2.48,
            "gps_lat":   13.1988,
            "gps_lon":   77.7068,
        }
    """

    # ── Tuning parameters ────────────────────────────────────────────────────
    MOVING_AVG_WINDOW: int   = 3      # hours each side for smoothing
    WEIGHT_DROP_PCT:   float = 0.05   # 5% abrupt drop triggers flag
    MIN_HOURS_FOR_MA:  int   = 2      # need at least this many points

    TEMP_CONSEC_HOURS: int   = 2      # consecutive hours above threshold → breach

    def detect_weight_loss(
        self,
        telemetry_data: list[TelemetryRecord],
    ) -> list[AnomalyDict]:
        """
        Moving-Average weight drop detector.

        Algorithm:
          1. Smooth the weight series using a centred moving average of window
             size MOVING_AVG_WINDOW to eliminate ±1 kg sensor noise.
          2. Walk consecutive (smoothed_i, smoothed_{i+1}) pairs.
          3. If the drop between adjacent smoothed values exceeds 5% of the
             smoothed value at i, flag TELEMETRY_WEIGHT_DROP.

        Returns a list of anomaly dicts (one per distinct drop event).
        """
        if len(telemetry_data) < self.MIN_HOURS_FOR_MA + 1:
            logger.warning("Not enough telemetry records for weight analysis (%d records).", len(telemetry_data))
            return []

        # Safe extraction: skip records that are malformed
        weights:    list[float] = []
        timestamps: list[str]   = []
        for idx, r in enumerate(telemetry_data):
            try:
                w = float(r["weight_kg"])
                t = str(r["timestamp"])
                weights.append(w)
                timestamps.append(t)
            except (KeyError, TypeError, ValueError) as exc:
                logger.warning(
                    "detect_weight_loss: skipping malformed record at index %d — %s", idx, exc
                )

        if len(weights) < self.MIN_HOURS_FOR_MA + 1:
            logger.warning(
                "detect_weight_loss: too few valid records after sanitisation (%d).", len(weights)
            )
            return []

        n = len(weights)

        # ── Step 1: Build smoothed series (centred moving average) ──────────
        smoothed: list[float] = []
        for i in range(n):
            lo  = max(0, i - self.MOVING_AVG_WINDOW)
            hi  = min(n, i + self.MOVING_AVG_WINDOW + 1)
            smoothed.append(sum(weights[lo:hi]) / (hi - lo))

        # ── Step 2: Detect abrupt drops in the smoothed series ──────────────
        anomalies: list[AnomalyDict] = []

        for i in range(1, n):
            prev = smoothed[i - 1]
            curr = smoothed[i]

            if prev == 0:
                continue  # avoid division by zero

            drop_fraction = (prev - curr) / prev   # positive = drop

            if drop_fraction > self.WEIGHT_DROP_PCT:
                dropped_kg = round(prev - curr, 2)
                anomalies.append({
                    "flag_type":   "TELEMETRY_WEIGHT_DROP",
                    "description": (
                        f"Moving-average weight dropped by {dropped_kg} kg "
                        f"({drop_fraction * 100:.1f}%) between "
                        f"{timestamps[i-1]} and {timestamps[i]}. "
                        "Possible cargo removal / theft detected."
                    ),
                    "variance":    -dropped_kg,   # negative = loss
                    "hour_index":  i,
                    "timestamp":   timestamps[i],
                })

        return anomalies

    def detect_temp_breach(
        self,
        telemetry_data: list[TelemetryRecord],
        threshold_c: float = 5.0,
    ) -> list[AnomalyDict]:
        """
        Consecutive-hour SLA temperature breach detector.

        Algorithm:
          1. Walk the temperature series hour by hour.
          2. Maintain a counter of consecutive hours above threshold_c.
          3. When the counter reaches TEMP_CONSEC_HOURS, emit a breach anomaly.
          4. Keep extending the same breach record until temperature drops below
             threshold (avoids multiple flags for one continuous event).

        Returns a list of anomaly dicts (one per distinct breach window).
        """
        if not telemetry_data:
            return []

        anomalies:     list[AnomalyDict] = []
        consec_count:  int   = 0
        breach_start:  str | None = None
        breach_active: bool  = False
        peak_temp:     float = -999.0

        for idx, record in enumerate(telemetry_data):
            try:
                temp = float(record["temp_c"])
                ts   = str(record["timestamp"])
            except (KeyError, TypeError, ValueError) as exc:
                logger.warning(
                    "detect_temp_breach: skipping malformed record at index %d — %s", idx, exc
                )
                continue

            if temp > threshold_c:
                consec_count += 1
                peak_temp     = max(peak_temp, temp)

                if consec_count == 1:
                    breach_start = ts   # record when exceedance began

                if consec_count >= self.TEMP_CONSEC_HOURS and not breach_active:
                    # Threshold crossed for required consecutive hours → flag it
                    anomalies.append({
                        "flag_type":   "SLA_TEMP_BREACH",
                        "description": (
                            f"Temperature exceeded SLA threshold of {threshold_c}°C "
                            f"for {consec_count}+ consecutive hours starting at "
                            f"{breach_start}. Peak recorded: {peak_temp:.1f}°C. "
                            "Cold-chain integrity may be compromised."
                        ),
                        "variance":   round(peak_temp - threshold_c, 2),
                        "timestamp":  breach_start,
                    })
                    breach_active = True   # don't re-flag same event

            else:
                # Temperature back within limits — reset
                consec_count  = 0
                breach_start  = None
                breach_active = False
                peak_temp     = -999.0

        return anomalies

    def analyze(
        self,
        telemetry_data: list[TelemetryRecord],
        temp_threshold_c: float = 5.0,
    ) -> list[AnomalyDict]:
        """
        Convenience method: run both detectors and return combined anomaly list.
        """
        if not telemetry_data:
            logger.info("No telemetry data provided; skipping forensic analysis.")
            return []

        weight_anomalies = self.detect_weight_loss(telemetry_data)
        temp_anomalies   = self.detect_temp_breach(telemetry_data, threshold_c=temp_threshold_c)

        all_anomalies = weight_anomalies + temp_anomalies

        logger.info(
            "TelemetryForensics: %d weight anomaly/ies, %d temp anomaly/ies detected.",
            len(weight_anomalies),
            len(temp_anomalies),
        )

        return all_anomalies
