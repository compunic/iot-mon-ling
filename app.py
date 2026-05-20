from flask import Flask, request, jsonify, render_template, redirect
import sqlite3

from datetime import datetime, timedelta

import pytz

app = Flask(__name__)

DB = "database.db"

# =====================================================
# TIMEZONE
# =====================================================
TZ = pytz.timezone('Asia/Jakarta')

# =====================================================
# DATABASE
# =====================================================
def init_db():

    conn = sqlite3.connect(DB)

    c = conn.cursor()

    c.execute("""

    CREATE TABLE IF NOT EXISTS sensor_data (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nama_esp TEXT,

        suhu REAL,
        kelembaban REAL,
        amonia REAL,

        jarak_pakan REAL,
        kapasitas_pakan REAL,

        status TEXT,

        created_at TEXT

    )

    """)

    conn.commit()
    conn.close()

init_db()

# =====================================================
# GET TIME WIB
# =====================================================
def now_wib():

    return datetime.now(TZ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

# =====================================================
# AUTO STATUS
# =====================================================
def generate_status(suhu, amonia):

    if suhu >= 33 or amonia >= 30:
        return "BAHAYA"

    elif suhu >= 30 or amonia >= 20:
        return "WASPADA"

    return "AMAN"

# =====================================================
# RECEIVE DATA ESP32
# =====================================================
@app.route('/receive', methods=['POST'])
def receive():

    data = request.json

    try:

        nama_esp = data.get(
            "nama_esp",
            "Unknown"
        )

        suhu = float(
            data.get("suhu", 0)
        )

        kelembaban = float(
            data.get("kelembaban", 0)
        )

        amonia = float(
            data.get("amonia", 0)
        )

        jarak_pakan = float(
            data.get("jarak_pakan", 0)
        )

        kapasitas_pakan = float(
            data.get("kapasitas_pakan", 0)
        )

        status = generate_status(
            suhu,
            amonia
        )

        conn = sqlite3.connect(DB)

        c = conn.cursor()

        c.execute("""

        INSERT INTO sensor_data (

            nama_esp,

            suhu,
            kelembaban,
            amonia,

            jarak_pakan,
            kapasitas_pakan,

            status,

            created_at

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            nama_esp,

            suhu,
            kelembaban,
            amonia,

            jarak_pakan,
            kapasitas_pakan,

            status,

            now_wib()

        ))

        conn.commit()
        conn.close()

        return jsonify({

            "success": True

        })

    except Exception as e:

        return jsonify({

            "success": False,
            "error": str(e)

        })

# =====================================================
# API LAST ALL DEVICES
# =====================================================
@app.route('/api/latest-all')
def latest_all():

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    c.execute("""

    SELECT *
    FROM sensor_data

    WHERE id IN (

        SELECT MAX(id)
        FROM sensor_data
        GROUP BY nama_esp

    )

    ORDER BY nama_esp ASC

    """)

    rows = c.fetchall()

    conn.close()

    return jsonify([

        dict(x)

        for x in rows

    ])

# =====================================================
# API HISTORY
# =====================================================
@app.route('/api/history')
def history():

    device = request.args.get(
        "device"
    )

    filter_type = request.args.get(
        "filter",
        "hour"
    )

    start_custom = request.args.get(
        "start"
    )

    end_custom = request.args.get(
        "end"
    )

    now = datetime.now(TZ)

    # ==========================================
    # FILTER TIME
    # ==========================================
    if filter_type == "minute":

        start = now - timedelta(hours=1)

    elif filter_type == "hour":

        start = now - timedelta(days=1)

    elif filter_type == "day":

        start = now - timedelta(days=7)

    elif filter_type == "week":

        start = now - timedelta(days=30)

    elif filter_type == "month":

        start = now - timedelta(days=365)

    elif filter_type == "custom":

        start = datetime.strptime(
            start_custom,
            "%Y-%m-%dT%H:%M"
        )

        end = datetime.strptime(
            end_custom,
            "%Y-%m-%dT%H:%M"
        )

    else:

        start = now - timedelta(hours=1)

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    # ==========================================
    # CUSTOM RANGE
    # ==========================================
    if filter_type == "custom":

        c.execute("""

        SELECT *
        FROM sensor_data

        WHERE nama_esp = ?
        AND created_at BETWEEN ? AND ?

        ORDER BY created_at ASC

        """, (

            device,

            start.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            end.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        ))

    # ==========================================
    # NORMAL FILTER
    # ==========================================
    else:

        c.execute("""

        SELECT *
        FROM sensor_data

        WHERE nama_esp = ?
        AND created_at >= ?

        ORDER BY created_at ASC

        """, (

            device,

            start.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        ))

    rows = c.fetchall()

    conn.close()

    return jsonify([

        dict(x)

        for x in rows

    ])

# =====================================================
# DASHBOARD
# =====================================================
@app.route('/')
def dashboard():

    return render_template(
        "dashboard.html"
    )

# =====================================================
# ADMIN PANEL
# =====================================================
@app.route('/admin')
def admin():

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    c.execute("""

    SELECT *
    FROM sensor_data

    ORDER BY id DESC

    LIMIT 200

    """)

    data = c.fetchall()

    conn.close()

    return render_template(

        "admin.html",

        data=data

    )

# =====================================================
# DELETE ALL DATA
# =====================================================
@app.route('/delete-all')
def delete_all():

    conn = sqlite3.connect(DB)

    c = conn.cursor()

    c.execute(
        "DELETE FROM sensor_data"
    )

    conn.commit()
    conn.close()

    return redirect('/admin')

# =====================================================
# SERVER STATUS
# =====================================================
@app.route('/status')
def status():

    return jsonify({

        "server": "online",

        "timezone": "Asia/Jakarta",

        "time": now_wib()

    })

# =====================================================
# RUN SERVER
# =====================================================
if __name__ == '__main__':

    app.run(

        host='0.0.0.0',

        port=5002,

        debug=True

    )
