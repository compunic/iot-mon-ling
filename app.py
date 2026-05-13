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
# GET CURRENT TIME WIB
# =====================================================
def now_wib():

    return datetime.now(TZ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

# =====================================================
# RECEIVE DATA FROM ESP32
# =====================================================
@app.route('/receive', methods=['POST'])
def receive():

    data = request.json

    try:

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

            data.get("nama_esp"),

            data.get("suhu"),
            data.get("kelembaban"),
            data.get("amonia"),

            data.get("jarak_pakan"),
            data.get("kapasitas_pakan"),

            data.get("status"),

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
# API LAST DATA
# =====================================================
@app.route('/api/latest')
def latest():

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    c.execute("""

    SELECT * FROM sensor_data

    ORDER BY id DESC

    LIMIT 1

    """)

    data = c.fetchone()

    conn.close()

    if data:

        return jsonify(dict(data))

    return jsonify({})

# =====================================================
# API HISTORY
# =====================================================
@app.route('/api/history')
def history():

    filter_type = request.args.get(
        "filter",
        "hour"
    )

    now = datetime.now(TZ)

    if filter_type == "minute":

        start = now - timedelta(minutes=60)

    elif filter_type == "day":

        start = now - timedelta(days=1)

    elif filter_type == "week":

        start = now - timedelta(weeks=1)

    elif filter_type == "month":

        start = now - timedelta(days=30)

    else:

        start = now - timedelta(hours=1)

    start_str = start.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    c.execute("""

    SELECT * FROM sensor_data

    WHERE created_at >= ?

    ORDER BY id ASC

    """, (start_str,))

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
# ADMIN PAGE
# =====================================================
@app.route('/admin')
def admin():

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    c.execute("""

    SELECT * FROM sensor_data

    ORDER BY id DESC

    LIMIT 100

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