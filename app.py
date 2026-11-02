import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import pandas as pd
import mysql.connector
from mysql.connector import Error as MySQLError
import psycopg2
from psycopg2.extras import RealDictCursor

# Keep local development on MySQL, while using PostgreSQL when DATABASE_URL
# is provided by Neon/another PostgreSQL host.
Error = (MySQLError, psycopg2.Error)
from analysis.weather_analysis import validate_weather_csv, build_summary, create_charts

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")
UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
CHART_FOLDER = os.path.join(app.root_path, "static", "charts")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHART_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"csv"}

def get_db():
    """Connect to hosted PostgreSQL when DATABASE_URL is set; otherwise use local MySQL."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        return psycopg2.connect(database_url)
    # Local development remains compatible with the original MySQL setup.
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", os.getenv("MYSQL_HOST", os.getenv("MYSQLHOST", "localhost"))),
        port=int(os.getenv("DB_PORT", os.getenv("MYSQL_PORT", os.getenv("MYSQLPORT", "3306")))),
        user=os.getenv("DB_USER", os.getenv("MYSQL_USER", os.getenv("MYSQLUSER", "root"))),
        password=os.getenv("DB_PASSWORD", os.getenv("MYSQL_PASSWORD", os.getenv("MYSQLPASSWORD", ""))),
        database=os.getenv("DB_NAME", os.getenv("MYSQL_DATABASE", os.getenv("MYSQLDATABASE", "weather_analysis"))),
    )

def get_cursor(conn, dictionary=False):
    """Return a regular or dictionary cursor for either supported database."""
    if os.getenv("DATABASE_URL", "").strip():
        return conn.cursor(cursor_factory=RealDictCursor) if dictionary else conn.cursor()
    return conn.cursor(dictionary=dictionary)

def close_connection(conn):
    if conn:
        try:
            conn.close()
        except Exception:
            pass

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    try:
        conn = get_db()
        cur = get_cursor(conn, dictionary=True)
        cur.execute("SELECT COUNT(*) AS total, AVG(temperature) AS avg_temp, AVG(humidity) AS avg_humidity, SUM(rainfall) AS total_rain FROM weather_records")
        stats = cur.fetchone()
        cur.execute("SELECT DISTINCT location FROM weather_records ORDER BY location")
        locations = [r["location"] for r in cur.fetchall()]
        cur.close(); conn.close()
    except Error:
        stats = {"total": 0, "avg_temp": None, "avg_humidity": None, "total_rain": None}
        locations = []
    return render_template("index.html", stats=stats, locations=locations)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename:
            flash("Please choose a CSV file.", "error")
            return redirect(url_for("upload"))
        if not allowed_file(file.filename):
            flash("Only .csv files are supported.", "error")
            return redirect(url_for("upload"))
        filename = secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)
        try:
            df, quality = validate_weather_csv(path)
            if df.empty:
                flash("No valid records found. Check the data quality report below.", "error")
                return render_template("upload.html", quality=quality)
            conn = get_db()
            cur = get_cursor(conn)
            sql = """INSERT INTO weather_records
                     (observation_date, location, temperature, humidity, rainfall)
                     VALUES (%s, %s, %s, %s, %s)"""
            rows = [
                (r.observation_date.date(), r.location, float(r.temperature),
                 float(r.humidity), float(r.rainfall))
                for r in df.itertuples(index=False)
            ]
            # Duplicate identity: same calendar date AND same location.
            # Same date at another location is a valid separate observation.
            cur.execute("SELECT observation_date, location FROM weather_records")
            existing = {(str(d), str(loc).strip().casefold()) for d, loc in cur.fetchall()}
            accepted = []
            duplicate_details = []
            for row in rows:
                key = (str(row[0]), str(row[1]).strip().casefold())
                if key in existing:
                    duplicate_details.append({"date": str(row[0]), "location": row[1]})
                    continue
                accepted.append(row)
                existing.add(key)  # also catches duplicates inside this CSV
            if accepted:
                cur.executemany(sql, accepted)
            conn.commit()
            inserted = len(accepted)
            cur.close(); conn.close()
            quality["duplicate_rows"] = len(duplicate_details)
            quality["duplicate_details"] = duplicate_details
            quality["rejected_rows"] += len(duplicate_details)
            flash(f"Imported {inserted} new records; skipped {len(duplicate_details)} duplicate records.", "success")
            return render_template("upload.html", quality=quality, inserted=inserted)
        except Exception as exc:
            flash(f"Upload could not be processed: {exc}", "error")
            return redirect(url_for("upload"))
    return render_template("upload.html")

@app.route("/analysis")
def analysis():
    location = request.args.get("location", "").strip()
    try:
        conn = get_db()
        query = "SELECT observation_date, location, temperature, humidity, rainfall FROM weather_records"
        params = ()
        if location:
            query += " WHERE location = %s"
            params = (location,)
        query += " ORDER BY observation_date"
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        summary = build_summary(df)
        if not df.empty:
            create_charts(df, CHART_FOLDER)
        return render_template("analysis.html", summary=summary, location=location, has_data=not df.empty)
    except Exception as exc:
        flash(f"Could not load analysis: {exc}", "error")
        return render_template("analysis.html", summary={}, location=location, has_data=False)

@app.route("/records")
def records():
    location = request.args.get("location", "").strip()
    try:
        conn = get_db()
        cur = get_cursor(conn, dictionary=True)
        query = "SELECT record_id, observation_date, location, temperature, humidity, rainfall FROM weather_records"
        params = ()
        if location:
            query += " WHERE location = %s"
            params = (location,)
        query += " ORDER BY observation_date DESC LIMIT 500"
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close(); conn.close()
    except Error as exc:
        rows = []
        flash(f"Database error: {exc}", "error")
    return render_template("records.html", rows=rows, location=location)

@app.route("/records/<int:record_id>/delete", methods=["POST"])
def delete_record(record_id):
    """Delete one weather observation. This action is POST-only."""
    conn = None
    cur = None
    try:
        conn = get_db()
        cur = get_cursor(conn)
        cur.execute("DELETE FROM weather_records WHERE record_id = %s", (record_id,))
        deleted = cur.rowcount
        conn.commit()
        if deleted:
            flash(f"Weather record #{record_id} deleted successfully.", "success")
        else:
            flash(f"Record #{record_id} was not found. It may already be deleted.", "error")
    except Error as exc:
        if conn:
            conn.rollback()
        flash(f"Could not delete record: {exc}", "error")
    finally:
        if cur:
            cur.close()
        if conn:
            close_connection(conn)
    return redirect(url_for("records"))


@app.route("/records/delete-all", methods=["POST"])
def delete_all_records():
    """Delete all weather observations after the user confirms in the UI."""
    conn = None
    cur = None
    try:
        conn = get_db()
        cur = get_cursor(conn)
        cur.execute("DELETE FROM weather_records")
        deleted = cur.rowcount
        conn.commit()
        flash(f"Deleted {deleted} weather record(s).", "success")
    except Error as exc:
        if conn:
            conn.rollback()
        flash(f"Could not delete weather records: {exc}", "error")
    finally:
        if cur:
            cur.close()
        if conn:
            close_connection(conn)
    return redirect(url_for("records"))


@app.route("/api/health")
def health():
    try:
        conn = get_db()
        if not os.getenv("DATABASE_URL", "").strip():
            conn.ping(reconnect=True, attempts=1, delay=0)
        else:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        conn.close()
        return jsonify({"status": "ok", "database": "connected"})
    except Error:
        return jsonify({"status": "error", "database": "disconnected"}), 503

@app.route("/api/summary")
def api_summary():
    location = request.args.get("location", "").strip()
    try:
        conn = get_db()
        query = "SELECT observation_date, location, temperature, humidity, rainfall FROM weather_records"
        params = ()
        if location:
            query += " WHERE location = %s"
            params = (location,)
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        return jsonify(build_summary(df))
    except Error as exc:
        return jsonify({"error": str(exc)}), 500

@app.route("/charts/<path:filename>")
def charts(filename):
    return send_from_directory(CHART_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "True").lower() == "true")

