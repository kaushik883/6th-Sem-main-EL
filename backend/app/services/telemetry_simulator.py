"""
telemetry_simulator.py
======================
Virtual E&I Telemetry Simulator — Service Module for LogiSight.

Generates 24 hours of realistic hourly sensor readings for a shipment.
This is called automatically when a Quote is accepted by the client so that
the TelemetryForensics engine always has data to work with at invoice analysis time.

For testing purposes, inject fraud patterns by setting is_fraud=True:
  - A sudden 50 kg weight drop at hour 12  (simulates cargo theft)
  - A 15°C temperature spike from hours 12–15 (simulates cold-chain SLA breach)
"""

from __future__ import annotations

import datetime
import logging
import math
import random
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sensor noise constants
# ---------------------------------------------------------------------------
HOURS            = 24
NOISE_WEIGHT_KG  = 1.0   # ± kg  — realistic sensor jitter
NOISE_TEMP_C     = 0.5   # ± °C  — realistic sensor jitter
BASELINE_TEMP_C  = 2.5   # °C   — nominal cold-chain temperature

# Fraud injection constants
FRAUD_HOUR        = 12   # hour index at which theft is injected
THEFT_DROP_KG     = 50.0 # kg drop simulating cargo removal
TEMP_SPIKE_START  = 12   # hour index where temperature spike begins
TEMP_SPIKE_HOURS  = 4    # number of consecutive hours above threshold
TEMP_SPIKE_VALUE  = 15.0 # °C — well above the 5°C SLA threshold

# GPS baseline: Kempegowda International Airport, Bengaluru
BASE_LAT  = 13.1986
BASE_LON  = 77.7066
GPS_DRIFT = 0.0002  # degrees per hour — simulates vehicle movement


def generate_telemetry(
    quote_id: int,
    base_weight: float,
    is_fraud: bool = False,
    start_time: datetime.datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Generate 24 hourly E&I sensor readings for a shipment.

    Parameters
    ----------
    quote_id    : The shipment / quote identifier (used only for logging).
    base_weight : The declared gross weight of the cargo in kg.
                  All sensor readings are anchored to this value ± noise.
    is_fraud    : If True, inject a cargo-theft weight drop and a
                  cold-chain temperature SLA breach at hour 12.
    start_time  : UTC datetime for hour-0. Defaults to the current UTC hour.

    Returns
    -------
    A list of 24 dicts, each with keys:
        timestamp (ISO-8601), weight_kg, temp_c, gps_lat, gps_lon
    """
    if base_weight <= 0:
        logger.warning(
            "generate_telemetry: quote %s has non-positive base_weight=%.2f; "
            "defaulting to 1.0 kg.",
            quote_id, base_weight,
        )
        base_weight = 1.0

    if start_time is None:
        start_time = datetime.datetime.utcnow().replace(
            minute=0, second=0, microsecond=0
        )

    readings: list[dict[str, Any]] = []
    current_weight = base_weight

    for hour in range(HOURS):
        ts = start_time + datetime.timedelta(hours=hour)

        # ── Weight ───────────────────────────────────────────────────────────
        if is_fraud and hour == FRAUD_HOUR:
            # Clamp the drop so weight never goes negative
            current_weight = max(0.0, current_weight - THEFT_DROP_KG)

        weight_noise   = random.uniform(-NOISE_WEIGHT_KG, NOISE_WEIGHT_KG)
        weight_reading = round(max(0.0, current_weight + weight_noise), 2)

        # ── Temperature ──────────────────────────────────────────────────────
        if is_fraud and TEMP_SPIKE_START <= hour < TEMP_SPIKE_START + TEMP_SPIKE_HOURS:
            temp_base = TEMP_SPIKE_VALUE
        else:
            temp_base = BASELINE_TEMP_C

        temp_noise   = random.uniform(-NOISE_TEMP_C, NOISE_TEMP_C)
        temp_reading = round(temp_base + temp_noise, 2)

        # ── GPS (simulate vehicle moving away from origin airport) ────────────
        lat = round(
            BASE_LAT + hour * GPS_DRIFT + random.uniform(-0.00005, 0.00005), 6
        )
        lon = round(
            BASE_LON
            + hour * GPS_DRIFT * math.cos(math.radians(BASE_LAT))
            + random.uniform(-0.00005, 0.00005),
            6,
        )

        readings.append({
            "timestamp": ts.isoformat() + "Z",
            "weight_kg": weight_reading,
            "temp_c":    temp_reading,
            "gps_lat":   lat,
            "gps_lon":   lon,
        })

    logger.info(
        "generate_telemetry: generated %d readings for quote %s "
        "(base_weight=%.2f kg, fraud=%s).",
        len(readings), quote_id, base_weight, is_fraud,
    )
    return readings
