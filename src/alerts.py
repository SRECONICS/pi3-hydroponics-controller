"""
alerts.py — Send Telegram push notifications for critical events.
"""

from __future__ import annotations
import logging, time
import config

log = logging.getLogger(__name__)
_last_alert: dict[str, float] = {}
ALERT_COOLDOWN = 1800  # don't spam: min 30 min between same alert type

def _send(text: str) -> bool:
    if not config.TELEGRAM_TOKEN or not config.TELEGRAM_CHAT_ID:
        log.info("Telegram not configured — alert suppressed: %s", text)
        return False
    try:
        import requests
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, json={
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text":    text,
            "parse_mode": "Markdown",
        }, timeout=10)
        return r.status_code == 200
    except Exception as e:
        log.warning("Telegram send failed: %s", e)
        return False

def _throttled(key: str) -> bool:
    now = time.time()
    if now - _last_alert.get(key, 0) < ALERT_COOLDOWN:
        return True
    _last_alert[key] = now
    return False

def check_and_alert(data: dict, actions: list[str]):
    """Evaluate sensor snapshot and fire Telegram alerts for anomalies."""
    ph     = data.get("ph", 0)
    ec     = data.get("ec_us_cm", 0)
    level  = data.get("level_pct", 100)
    wtemp  = data.get("water_temp_c") or 0

    if not _throttled("ph_low") and ph < 5.0:
        _send(f"⚠️ *pH CRITICAL LOW* — pH={ph:.2f}  (target {config.TARGET_PH_MIN}–{config.TARGET_PH_MAX})")
    if not _throttled("ph_high") and ph > 7.5:
        _send(f"⚠️ *pH CRITICAL HIGH* — pH={ph:.2f}")
    if not _throttled("ec_low") and ec < 800:
        _send(f"⚠️ *EC CRITICALLY LOW* — {ec:.0f} µS/cm  (target {config.TARGET_EC_MIN}–{config.TARGET_EC_MAX})")
    if not _throttled("level") and level < config.TANK_LOW_WARN_PCT:
        _send(f"💧 *TANK LOW* — {level:.0f}% remaining. Refill soon!")
    if not _throttled("temp_high") and wtemp > 28:
        _send(f"🌡️ *HIGH WATER TEMP* — {wtemp:.1f}°C (target < {config.TARGET_TEMP_MAX}°C)")

    if actions:
        summary = "\n".join(f"  • {a}" for a in actions)
        _send(f"🌱 *Auto-Dose Event*\n{summary}")
