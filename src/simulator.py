"""
simulator.py — Hardware-free simulation mode for development and testing.

Usage:
    python main.py --simulate

Overrides sensors.read_all() with realistic synthetic data that drifts
slowly over time, allowing the full control loop and web dashboard to run
without any physical hardware.
"""

from __future__ import annotations
import math, random, time

_t0 = time.time()

def simulated_readings() -> dict:
    t = time.time() - _t0
    # pH drifts between 5.4 – 6.8 on a slow sine wave + small noise
    ph = 6.0 + 0.4 * math.sin(t / 600) + random.gauss(0, 0.03)
    # EC trends down slowly as plants consume nutrients
    ec = 1600 - (t / 60) * 0.5 + 100 * math.sin(t / 900) + random.gauss(0, 15)
    # Water temperature tracks a 24-hour sine (peak afternoon)
    hour_frac = (t % 86400) / 86400
    water_t = 22 + 3 * math.sin(2 * math.pi * hour_frac - math.pi / 2)
    level = max(10, 95 - t / 600)        # tank drains slowly
    air_t = water_t + random.gauss(1, 0.3)
    air_rh = 65 + 5 * math.sin(t / 300) + random.gauss(0, 1)

    return {
        "ph":           round(ph, 2),
        "ec_us_cm":     round(max(0, ec), 1),
        "water_temp_c": round(water_t, 2),
        "level_pct":    round(level, 1),
        "air_temp_c":   round(air_t, 1),
        "air_rh_pct":   round(min(100, air_rh), 1),
    }
