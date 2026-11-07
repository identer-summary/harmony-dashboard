import os
from datetime import datetime

from flask import Flask, jsonify, render_template, request


app = Flask(__name__)


reports_db = {
    "202-603": {
        "building": "202",
        "unit": "603",
        "avgNoise": 45,
        "maxNoise": 60,
        "status": "주의",
        "vibration": 0.0015,
        "frequency": 150,
        "source": "demo",
        "time": "22:41:18",
    },
    "202-503": {
        "building": "202",
        "unit": "503",
        "avgNoise": 55,
        "maxNoise": 82,
        "status": "심각",
        "vibration": 0.0021,
        "frequency": 120,
        "source": "demo",
        "time": "23:17:42",
    },
}


def _number(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _status_from_average(avg_noise):
    if avg_noise >= 50:
        return "심각"
    if avg_noise >= 40:
        return "주의"
    return "양호"


@app.post("/api/report")
def receive_report():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"status": "error", "message": "JSON 형식의 측정값이 필요합니다."}), 400

    building = str(payload.get("building", "미상")).strip() or "미상"
    unit = str(payload.get("unit", "미상")).strip() or "미상"
    avg_noise = _number(payload.get("avgNoise"))

    report = dict(payload)
    report.update(
        {
            "building": building,
            "unit": unit,
            "avgNoise": avg_noise,
            "maxNoise": _number(payload.get("maxNoise"), avg_noise),
            "vibration": _number(payload.get("vibration")),
            "frequency": _number(payload.get("frequency")),
            "status": _status_from_average(avg_noise),
            "source": payload.get("source", "sensor"),
            "time": datetime.now().strftime("%H:%M:%S"),
        }
    )

    key = f"{building}-{unit}"
    reports_db.setdefault(key, {}).update(report)
    return jsonify({"status": "success", "key": key, "report": reports_db[key]})


@app.get("/api/data")
def get_data():
    return jsonify(reports_db)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/")
def dashboard():
    demo_mode = os.getenv("DEMO_MODE", "true").lower() not in {"0", "false", "off"}
    return render_template("dashboard.html", reports=reports_db, demo_mode=demo_mode)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
