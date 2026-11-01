"""
main.py — Entry point for the Raspberry Pi 3 Hydroponics Controller.

Usage:
    python main.py              # production (real hardware)
    python main.py --simulate   # simulation mode (no GPIO required)
    python main.py --once       # single read-and-decide cycle then exit

Service: see ../systemd/hydroponics.service
"""

from __future__ import annotations
import sys, time, argparse, logging, threading, signal
import config, data_logger, dosing, alerts, web_dashboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("main")

def parse_args():
    p = argparse.ArgumentParser(description="Raspberry Pi 3 Hydroponics Controller")
    p.add_argument("--simulate", action="store_true",
                   help="Use synthetic sensor data (no hardware needed)")
    p.add_argument("--once", action="store_true",
                   help="Run one cycle and exit")
    p.add_argument("--no-web", action="store_true",
                   help="Disable Flask web server")
    return p.parse_args()

def run_cycle(reader, simulate: bool) -> dict:
    """Read sensors, decide doses, log, alert. Returns sensor snapshot."""
    data = reader()
    data_logger.log_reading(data)
    web_dashboard.update_state(data)

    actions = []
    if not simulate:          # never fire real pumps in simulation
        actions = dosing.auto_adjust(data["ph"], data["ec_us_cm"])
        for action in actions:
            log.info("AUTO-DOSE: %s", action)
            data_logger.log_dose(action.split()[1].lower(), config.DOSE_DURATION_S)

    alerts.check_and_alert(data, actions)
    log.info("pH=%.2f  EC=%.0f µS/cm  H₂O=%.1f°C  Tank=%.0f%%",
             data["ph"], data["ec_us_cm"], data["water_temp_c"] or 0, data["level_pct"])
    return data

def main():
    args = parse_args()

    if args.simulate:
        log.info("⚠  SIMULATION MODE — no GPIO, synthetic sensor data")
        import simulator
        reader = simulator.simulated_readings
    else:
        import sensors
        reader = sensors.read_all

    data_logger.init_db()

    # Start Flask in a background thread
    if not args.no_web:
        t = threading.Thread(target=web_dashboard.run_server, daemon=True)
        t.start()
        log.info("Web dashboard on http://0.0.0.0:%d", config.FLASK_PORT)

    def _shutdown(sig, frame):
        log.info("Shutting down …")
        dosing.cleanup()
        sys.exit(0)
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT,  _shutdown)

    log.info("Hydroponics Controller started (Pi 3). Read interval: %ds",
             config.LOG_INTERVAL_S)

    if args.once:
        run_cycle(reader, args.simulate)
        dosing.cleanup()
        return

    while True:
        try:
            run_cycle(reader, args.simulate)
        except Exception as e:
            log.exception("Cycle error: %s", e)
        time.sleep(config.LOG_INTERVAL_S)

if __name__ == "__main__":
    main()
