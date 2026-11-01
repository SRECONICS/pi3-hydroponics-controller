"""
dosing.py — Peristaltic pump control via 4-channel relay board.

Safety features:
  • Cooldown between consecutive doses (config.DOSE_COOLDOWN_S)
  • Hourly dose counter with configurable hard limit
  • Context-manager cleans up GPIO on exit
"""

from __future__ import annotations
import time, logging, threading
from collections import defaultdict
from datetime import datetime
import config

log = logging.getLogger(__name__)

# Last-dose timestamps per pump channel
_last_dose: dict[int, float] = defaultdict(float)
_dose_counts: dict[str, int] = defaultdict(int)
_lock = threading.Lock()

PUMPS = {
    "ph_up":    config.GPIO_RELAY_PH_UP,
    "ph_down":  config.GPIO_RELAY_PH_DOWN,
    "nut_a":    config.GPIO_RELAY_NUT_A,
    "nut_b":    config.GPIO_RELAY_NUT_B,
}

def _init_gpio():
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        for pin in PUMPS.values():
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)  # HIGH = relay off (active-low)
    except Exception as e:
        log.warning("GPIO init failed (simulation mode?): %s", e)

def dose(pump_name: str, duration_s: float = None) -> bool:
    """
    Activate one pump for `duration_s` seconds.
    Returns True if dose was delivered, False if blocked by cooldown/limit.
    """
    if pump_name not in PUMPS:
        raise ValueError(f"Unknown pump: {pump_name!r}. Choose from {list(PUMPS)}")
    duration_s = duration_s or config.DOSE_DURATION_S
    pin = PUMPS[pump_name]
    hour_key = f"{pump_name}_{datetime.now().strftime('%Y%m%d%H')}"

    with _lock:
        now = time.time()
        elapsed = now - _last_dose[pin]
        if elapsed < config.DOSE_COOLDOWN_S:
            log.info("Dose blocked — cooldown %.0fs remaining for %s",
                     config.DOSE_COOLDOWN_S - elapsed, pump_name)
            return False
        if _dose_counts[hour_key] >= config.DOSE_MAX_PER_HOUR:
            log.warning("Dose blocked — hourly limit reached for %s", pump_name)
            return False
        _last_dose[pin] = now
        _dose_counts[hour_key] += 1

    log.info("Dosing %s for %.1f s", pump_name, duration_s)
    try:
        import RPi.GPIO as GPIO
        GPIO.output(pin, GPIO.LOW)   # energise relay
        time.sleep(duration_s)
        GPIO.output(pin, GPIO.HIGH)  # de-energise
    except ImportError:
        log.warning("RPi.GPIO not available — simulating pump %s ON for %.1f s",
                    pump_name, duration_s)
        time.sleep(duration_s)
    return True

def auto_adjust(ph: float, ec_us_cm: float) -> list[str]:
    """
    Evaluate current readings and dose as needed.
    Returns list of actions taken.
    """
    actions = []
    if ph < config.TARGET_PH_MIN:
        if dose("ph_up"):
            actions.append(f"Dosed pH-Up (pH={ph:.2f} < {config.TARGET_PH_MIN})")
    elif ph > config.TARGET_PH_MAX:
        if dose("ph_down"):
            actions.append(f"Dosed pH-Down (pH={ph:.2f} > {config.TARGET_PH_MAX})")

    if ec_us_cm < config.TARGET_EC_MIN:
        if dose("nut_a"):
            actions.append(f"Dosed Nutrient-A (EC={ec_us_cm:.0f} < {config.TARGET_EC_MIN})")
        if dose("nut_b"):
            actions.append(f"Dosed Nutrient-B (EC={ec_us_cm:.0f} < {config.TARGET_EC_MIN})")

    return actions

def cleanup():
    try:
        import RPi.GPIO as GPIO
        GPIO.cleanup(list(PUMPS.values()))
    except Exception:
        pass

# initialise pins on import (safe: just sets pin direction)
_init_gpio()
