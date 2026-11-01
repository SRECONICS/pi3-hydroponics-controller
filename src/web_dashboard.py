"""
web_dashboard.py — Flask web dashboard for real-time monitoring.

Endpoints:
  GET /              → HTML dashboard with Chart.js sparklines
  GET /api/latest    → JSON: latest sensor snapshot
  GET /api/history   → JSON: last 60 readings
  GET /api/doses     → JSON: last 20 dose events
  POST /api/dose     → Manual dose trigger (JSON body: {"pump":"ph_up"})
"""

from __future__ import annotations
import json, logging
from flask import Flask, jsonify, request, render_template_string
import data_logger, dosing, config

log = logging.getLogger(__name__)
app = Flask(__name__)

# ─── shared state updated by main loop ─────────────────────────────────────
_current: dict = {}

def update_state(data: dict):
    global _current
    _current = data

# ─── HTML template ───────────────────────────────────────────────────────────
_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hydroponics Dashboard</title>
<style>
  body{background:#0d1117;color:#e6edf3;font-family:system-ui;margin:0;padding:16px}
  h1{color:#39d353;font-size:1.4rem;margin:0 0 16px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px}
  .card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:14px}
  .label{font-size:.75rem;color:#8b949e;text-transform:uppercase;letter-spacing:.04em}
  .value{font-size:1.9rem;font-weight:700;color:#58a6ff;margin-top:4px}
  .unit{font-size:.8rem;color:#8b949e}
  .ok{color:#39d353}.warn{color:#f0b429}.crit{color:#f85149}
  table{width:100%;border-collapse:collapse;margin-top:24px;font-size:.85rem}
  th{background:#21262d;color:#8b949e;padding:6px 10px;text-align:left}
  td{border-top:1px solid #21262d;padding:6px 10px}
  footer{margin-top:32px;color:#484f58;font-size:.75rem}
</style>
</head>
<body>
<h1>🌱 Hydroponics Controller</h1>
<div class="grid" id="cards"></div>
<div id="dose-log"></div>
<footer>Raspberry Pi 3 · DevNode Technologies — refreshes every 15 s</footer>
<script>
async function refresh(){
  const [lat, doses] = await Promise.all([
    fetch('/api/latest').then(r=>r.json()),
    fetch('/api/doses').then(r=>r.json())
  ]);
  const d = lat.data || {};
  const metrics = [
    {label:'pH',         value:d.ph?.toFixed(2) ?? '--',         unit:'',         ok: d.ph>=5.8&&d.ph<=6.2},
    {label:'EC',         value:d.ec_us_cm?.toFixed(0) ?? '--',   unit:'µS/cm',    ok: d.ec_us_cm>=1400&&d.ec_us_cm<=1800},
    {label:'Water Temp', value:d.water_temp_c?.toFixed(1) ?? '--',unit:'°C',       ok: d.water_temp_c>=18&&d.water_temp_c<=26},
    {label:'Tank Level', value:d.level_pct?.toFixed(0) ?? '--',  unit:'%',        ok: d.level_pct>20},
    {label:'Air Temp',   value:d.air_temp_c?.toFixed(1) ?? '--', unit:'°C',       ok: true},
    {label:'Air RH',     value:d.air_rh_pct?.toFixed(0) ?? '--', unit:'%',        ok: true},
  ];
  document.getElementById('cards').innerHTML = metrics.map(m=>
    `<div class="card"><div class="label">${m.label}</div>
     <div class="value ${m.ok?'ok':'crit'}">${m.value} <span class="unit">${m.unit}</span></div></div>`
  ).join('');
  if(doses.data && doses.data.length){
    const rows = doses.data.map(e=>`<tr><td>${e.ts.slice(0,19)}</td><td>${e.pump}</td><td>${e.duration_s}s</td><td>${e.trigger}</td></tr>`).join('');
    document.getElementById('dose-log').innerHTML =
      '<h2 style="color:#8b949e;font-size:1rem;margin-top:24px">Recent Dose Events</h2>' +
      `<table><thead><tr><th>Time (UTC)</th><th>Pump</th><th>Duration</th><th>Trigger</th></tr></thead><tbody>${rows}</tbody></table>`;
  }
}
refresh(); setInterval(refresh, 15000);
</script>
</body></html>
"""

@app.route("/")
def index():
    return render_template_string(_TEMPLATE)

@app.route("/api/latest")
def api_latest():
    return jsonify({"ok": True, "data": _current})

@app.route("/api/history")
def api_history():
    return jsonify({"ok": True, "data": data_logger.latest_readings(60)})

@app.route("/api/doses")
def api_doses():
    return jsonify({"ok": True, "data": data_logger.recent_doses(20)})

@app.route("/api/dose", methods=["POST"])
def api_dose():
    body = request.get_json(force=True)
    pump = body.get("pump", "")
    if pump not in dosing.PUMPS:
        return jsonify({"ok": False, "error": "unknown pump"}), 400
    ok = dosing.dose(pump, body.get("duration_s"))
    if ok:
        data_logger.log_dose(pump, config.DOSE_DURATION_S, "manual")
    return jsonify({"ok": ok})

def run_server():
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT,
            debug=False, use_reloader=False)
