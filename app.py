from flask import Flask, request, render_template, redirect, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# -------------------------
# DATABASE SETUP
# -------------------------
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ph REAL,
            fac REAL,
            bather_load INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------------
# ROUTES
# -------------------------

# Entry page
@app.route("/")
def form():
    return render_template("form.html")

# Handle form submission
@app.route("/submit", methods=["POST"])
def submit():
    ph = request.form["ph"]
    fac = request.form["fac"]
    bather = request.form["bather"]

    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO logs (timestamp, ph, fac, bather_load) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), ph, fac, bather)
    )
    conn.commit()
    conn.close()

    return redirect("/")

# Return data as JSON (for graphs)
@app.route("/data")
def data():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT timestamp, ph, fac FROM logs")
    rows = c.fetchall()
    conn.close()

    return jsonify(rows)

# Graph page
@app.route("/graph")
def graph():
    return render_template("graph.html")

# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)