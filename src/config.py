"""
config.py — Centralised configuration for the Hydroponics Controller.
Edit this file to match your hardware wiring and grow parameters.
"""

# ─── GPIO pin numbers (BCM mode) ───────────────────────────────────────────
GPIO_RELAY_PH_UP    = 17   # peristaltic pump: pH-up solution
GPIO_RELAY_PH_DOWN  = 27   # peristaltic pump: pH-down solution
GPIO_RELAY_NUT_A    = 22   # peristaltic pump: nutrient A
GPIO_RELAY_NUT_B    = 23   # peristaltic pump: nutrient B

GPIO_TRIG           = 24   # HC-SR04 trigger
GPIO_ECHO           = 25   # HC-SR04 echo

# DS18B20 1-Wire device file (auto-detected by sensors.py if omitted)
DS18B20_DEVICE      = "/sys/bus/w1/devices/28-*/w1_slave"

# ─── MCP3008 SPI (via spidev bus 0) ────────────────────────────────────────
SPI_BUS             = 0
SPI_DEVICE          = 0
ADC_CH_PH           = 0    # MCP3008 channel for pH probe signal
ADC_CH_EC           = 1    # MCP3008 channel for EC/TDS signal
ADC_VREF            = 3.3  # reference voltage

# ─── pH calibration (linear: pH = slope * raw_voltage + offset) ────────────
PH_SLOPE            = -5.70    # calibrate with pH 4 and pH 7 buffers
PH_OFFSET           = 21.34

# ─── EC calibration (µS/cm per mV above baseline) ──────────────────────────
EC_SLOPE            = 1.22
EC_OFFSET           = 0.0
EC_TEMP_COEFF       = 0.02     # 2 % per °C compensation

# ─── Dosing parameters ──────────────────────────────────────────────────────
TARGET_PH_MIN       = 5.8
TARGET_PH_MAX       = 6.2
TARGET_EC_MIN       = 1400    # µS/cm
TARGET_EC_MAX       = 1800
TARGET_TEMP_MIN     = 18.0    # °C
TARGET_TEMP_MAX     = 26.0

DOSE_DURATION_S     = 2.0     # seconds per dosing pulse
DOSE_COOLDOWN_S     = 300     # wait between consecutive doses (seconds)
DOSE_MAX_PER_HOUR   = 6       # safety limit

# ─── Tank ───────────────────────────────────────────────────────────────────
TANK_EMPTY_CM       = 30.0    # HC-SR04 reading when tank is empty
TANK_FULL_CM        = 5.0     # reading when tank is full
TANK_LOW_WARN_PCT   = 20      # alert below this percent

# ─── Logging & Web ──────────────────────────────────────────────────────────
DB_PATH             = "/var/lib/hydroponics/data.db"
LOG_INTERVAL_S      = 60      # seconds between sensor readings
FLASK_PORT          = 5000
FLASK_HOST          = "0.0.0.0"

# ─── Telegram alerts ────────────────────────────────────────────────────────
# Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID in environment or override here.
import os
TELEGRAM_TOKEN      = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID    = os.getenv("TELEGRAM_CHAT_ID", "")
