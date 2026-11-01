"""
sensors.py — Read all analog and digital sensors.

Hardware:
  - pH probe    → MCP3008 ch0  (SPI)
  - EC/TDS      → MCP3008 ch1  (SPI)
  - DS18B20     → 1-Wire (GPIO 4)
  - HC-SR04     → GPIO 24/25
  - DHT22       → GPIO 18
"""

from __future__ import annotations
import time, glob, logging
import config

log = logging.getLogger(__name__)

# ─── MCP3008 via spidev ──────────────────────────────────────────────────────
def _spi_read_channel(channel: int) -> float:
    """Return voltage on MCP3008 channel (0-7)."""
    try:
        import spidev
        spi = spidev.SpiDev()
        spi.open(config.SPI_BUS, config.SPI_DEVICE)
        spi.max_speed_hz = 1_000_000
        cmd = [1, (8 + channel) << 4, 0]
        reply = spi.xfer2(cmd)
        spi.close()
        raw = ((reply[1] & 0x03) << 8) | reply[2]   # 10-bit value
        return (raw / 1023.0) * config.ADC_VREF
    except Exception as e:
        log.warning("SPI read failed: %s", e)
        return 0.0

# ─── pH ──────────────────────────────────────────────────────────────────────
def read_ph() -> float:
    voltage = _spi_read_channel(config.ADC_CH_PH)
    ph = config.PH_SLOPE * voltage + config.PH_OFFSET
    return round(max(0.0, min(14.0, ph)), 2)

# ─── EC / TDS ────────────────────────────────────────────────────────────────
def read_ec(water_temp_c: float = 25.0) -> float:
    """Return EC in µS/cm, temperature-compensated."""
    voltage = _spi_read_channel(config.ADC_CH_EC)
    ec_raw = config.EC_SLOPE * (voltage * 1000) + config.EC_OFFSET
    temp_factor = 1.0 + config.EC_TEMP_COEFF * (water_temp_c - 25.0)
    return round(max(0.0, ec_raw / temp_factor), 1)

# ─── DS18B20 water temperature ───────────────────────────────────────────────
def read_water_temp() -> float:
    """Read DS18B20 1-Wire sensor; returns °C or None on error."""
    try:
        devices = glob.glob(config.DS18B20_DEVICE)
        if not devices:
            return None
        with open(devices[0], "r") as f:
            lines = f.readlines()
        if lines[0].strip().endswith("YES"):
            raw = lines[1].split("t=")[-1].strip()
            return round(int(raw) / 1000.0, 2)
    except Exception as e:
        log.warning("DS18B20 error: %s", e)
    return None

# ─── HC-SR04 water level ─────────────────────────────────────────────────────
def read_water_level_cm() -> float:
    """Return HC-SR04 distance in cm."""
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(config.GPIO_TRIG, GPIO.OUT)
        GPIO.setup(config.GPIO_ECHO, GPIO.IN)
        GPIO.output(config.GPIO_TRIG, False)
        time.sleep(0.05)
        GPIO.output(config.GPIO_TRIG, True)
        time.sleep(0.00001)
        GPIO.output(config.GPIO_TRIG, False)
        t_start = t_end = time.time()
        timeout = time.time() + 0.04
        while GPIO.input(config.GPIO_ECHO) == 0 and time.time() < timeout:
            t_start = time.time()
        while GPIO.input(config.GPIO_ECHO) == 1 and time.time() < timeout:
            t_end = time.time()
        distance = (t_end - t_start) * 17150
        GPIO.cleanup([config.GPIO_TRIG, config.GPIO_ECHO])
        return round(distance, 1)
    except Exception as e:
        log.warning("HC-SR04 error: %s", e)
        return config.TANK_EMPTY_CM

def water_level_percent() -> float:
    cm = read_water_level_cm()
    empty = config.TANK_EMPTY_CM
    full  = config.TANK_FULL_CM
    pct = (empty - cm) / (empty - full) * 100
    return round(max(0.0, min(100.0, pct)), 1)

# ─── DHT22 air sensor ────────────────────────────────────────────────────────
def read_air(pin: int = 18):
    """Return (temp_c, humidity_pct) from DHT22."""
    try:
        import adafruit_dht, board
        dht = adafruit_dht.DHT22(getattr(board, f"D{pin}"))
        temp = dht.temperature
        hum  = dht.humidity
        dht.exit()
        return round(temp, 1), round(hum, 1)
    except Exception as e:
        log.warning("DHT22 error: %s", e)
        return None, None

# ─── Composite snapshot ──────────────────────────────────────────────────────
def read_all() -> dict:
    water_t = read_water_temp()
    return {
        "ph":           read_ph(),
        "ec_us_cm":     read_ec(water_t or 25.0),
        "water_temp_c": water_t,
        "level_pct":    water_level_percent(),
        "air_temp_c":   read_air()[0],
        "air_rh_pct":   read_air()[1],
    }
