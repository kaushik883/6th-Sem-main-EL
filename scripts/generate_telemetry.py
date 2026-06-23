"""
generate_telemetry.py
=====================
Virtual E&I Telemetry Simulator for LogiSight.

Generates 24 hours of hourly sensor data for a given shipment/quote.
Automatically reads the correct baseline weight from the database and saves 
the generated telemetry JSON directly to the quote.

Usage:
    cd backend
    source .venv/bin/activate
    python ../scripts/generate_telemetry.py --quote_id 42 --is_fraud
"""

import argparse
import json
import random
import datetime
import math
import asyncio
import sys
import os

# Add the backend directory to sys.path so we can import the app modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import AsyncSessionLocal
from app.models.quote import Quote
from sqlalchemy import select

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HOURS = 24
NOISE_WEIGHT_KG   = 1.0    # ± kg  — sensor jitter
NOISE_TEMP_C      = 0.5    # ± °C  — sensor jitter

# Fraud parameters
FRAUD_HOUR        = 12     # hour at which cargo theft is simulated
THEFT_DROP_KG     = 50.0   # sudden weight drop at fraud hour
TEMP_SPIKE_START  = 12     # first hour of temperature spike
TEMP_SPIKE_HOURS  = 4      # how many consecutive hours the spike lasts
TEMP_SPIKE_VALUE  = 15.0   # °C spike value (far above 5°C SLA threshold)

# Baseline GPS centre point
BASE_LAT = 13.1986
BASE_LON = 77.7066
GPS_DRIFT = 0.0002  # tiny GPS drift per hour

BASELINE_TEMP_C = 2.5      # nominal cold-chain temperature (°C)


def generate_telemetry(
    quote_id: int,
    base_weight: float,
    is_fraud: bool,
    start_time=None,
) -> list:
    if start_time is None:
        start_time = datetime.datetime.utcnow().replace(
            minute=0, second=0, microsecond=0
        )

    readings = []
    current_weight = base_weight

    for hour in range(HOURS):
        ts = start_time + datetime.timedelta(hours=hour)

        if is_fraud and hour == FRAUD_HOUR:
            current_weight -= THEFT_DROP_KG

        weight_noise   = random.uniform(-NOISE_WEIGHT_KG, NOISE_WEIGHT_KG)
        weight_reading = round(max(0.0, current_weight + weight_noise), 2)

        if is_fraud and TEMP_SPIKE_START <= hour < TEMP_SPIKE_START + TEMP_SPIKE_HOURS:
            temp_base = TEMP_SPIKE_VALUE
        else:
            temp_base = BASELINE_TEMP_C

        temp_noise   = random.uniform(-NOISE_TEMP_C, NOISE_TEMP_C)
        temp_reading = round(temp_base + temp_noise, 2)

        lat = round(BASE_LAT + hour * GPS_DRIFT + random.uniform(-0.00005, 0.00005), 6)
        lon = round(BASE_LON + hour * GPS_DRIFT * math.cos(math.radians(BASE_LAT))
                    + random.uniform(-0.00005, 0.00005), 6)

        readings.append({
            "timestamp": ts.isoformat() + "Z",
            "weight_kg": weight_reading,
            "temp_c":    temp_reading,
            "gps_lat":   lat,
            "gps_lon":   lon,
        })

    return readings


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate 24 h of simulated E&I telemetry for a LogiSight quote."
    )
    parser.add_argument("--quote_id", type=int, required=True, help="Quote / shipment ID")
    parser.add_argument("--is_fraud", action="store_true", help="Inject cargo-theft anomaly pattern")
    return parser.parse_args()


async def main():
    args = parse_args()

    print(f"\n{'='*60}")
    print(f"  LogiSight Virtual Telemetry Simulator")
    print(f"{'='*60}")
    
    async with AsyncSessionLocal() as db:
        quote = await db.get(Quote, args.quote_id)
        if not quote:
            print(f"❌ Error: Quote ID {args.quote_id} not found in database.")
            return

        base_weight = float(quote.gross_weight)
        
        print(f"  Quote ID    : {args.quote_id} (Found in DB)")
        print(f"  Base Weight : {base_weight} kg (Fetched from DB)")
        print(f"  Fraud Mode  : {'YES ⚠️' if args.is_fraud else 'No'}")
        print(f"{'='*60}\n")

        data = generate_telemetry(
            quote_id=args.quote_id,
            base_weight=base_weight,
            is_fraud=args.is_fraud,
        )

        print(f"{'Hour':<6} {'Timestamp':<26} {'Weight(kg)':<12} {'Temp(C)':<10} {'Lat':<12} {'Lon'}")
        print("-" * 80)
        for i, r in enumerate(data):
            flag = ""
            if args.is_fraud and i == FRAUD_HOUR:
                flag = " <- THEFT DROP"
            elif args.is_fraud and TEMP_SPIKE_START <= i < TEMP_SPIKE_START + TEMP_SPIKE_HOURS:
                flag = " <- TEMP SPIKE"
            print(
                f"{i:<6} {r['timestamp']:<26} {r['weight_kg']:<12} "
                f"{r['temp_c']:<10} {r['gps_lat']:<12} {r['gps_lon']}{flag}"
            )

        # Save to DB
        quote.telemetry_data = data
        await db.commit()
        print(f"\n✅ Successfully saved 24h of telemetry data directly to Quote {args.quote_id} in the database!")


if __name__ == "__main__":
    asyncio.run(main())
