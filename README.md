# Weather Data Analysis System

A beginner-friendly Flask web application that supports local MySQL and hosted PostgreSQL for analysing **historical weather observations**. It accepts CSV files, validates rows, stores valid records in MySQL, calculates daily/monthly statistics using Pandas and NumPy, and creates Matplotlib charts.

> This project analyses recorded data. It does **not** forecast future weather.

## GitHub and deployment
- `.env`, virtual environments, Python cache files, uploaded CSVs, and generated chart images are excluded from Git with `.gitignore`.
- Keep real database credentials only in the hosting provider's environment-variable settings; never commit `.env`.
- Production start command: `gunicorn app:app --bind 0.0.0.0:$PORT` (also included in `Procfile`).
- For a free demo, you can host the Flask app on Render and use a free Neon PostgreSQL database. In Render's environment variables, set `DATABASE_URL` to Neon’s pooled or direct connection string (keep `sslmode=require`) and set `SECRET_KEY` to a long random value.
- Before first launch, run `database/schema_postgresql.sql` in Neon’s SQL Editor. This creates the table expected by the app.
- Local development can continue using MySQL and the original `database/schema.sql`; the app uses PostgreSQL only when `DATABASE_URL` is set.
- Render free web services may sleep after inactivity, and local uploaded files/generated chart images are temporary. Database records are stored in Neon, not on the Render filesystem.

## 1. Requirements
- Python 3.10 or newer
- MySQL Server 8.x (or compatible)
- VS Code (recommended)
- Internet connection for Google Fonts and Lucide icons used by the UI

## 2. Setup

### Windows (PowerShell)
```powershell
# Open this project folder in VS Code terminal
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again.

### Create database
1. Start MySQL Server.
2. Open MySQL Workbench or MySQL command line.
3. Run the complete script `database/schema.sql`.

### Configure credentials
Copy `.env.example` to `.env` and update `DB_USER` and `DB_PASSWORD` to match your local MySQL account. The app also accepts the equivalent `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE` names. Do not share or commit `.env`.

### Run the application
```powershell
python app.py
```
Open `http://127.0.0.1:5000` in your browser.

## 3. First demo
1. Open **Upload dataset**.
2. Select `sample_weather.csv` from this project folder.
3. Review the data-quality report and import result.
4. Open **Analysis & charts** to view metrics, monthly summary and four charts.
5. Open **Weather records** to see saved MySQL rows. Use **Delete** to remove one row, or **Delete all records** to clear the table after confirming. These actions delete database rows only; they do not remove the original CSV file from your computer.

## 4. CSV format and units
Required column names (case-insensitive): `date`, `location`, `temperature`, `humidity`, `rainfall`.
- `date`: a date Pandas can parse (recommended `YYYY-MM-DD`)
- `location`: non-empty place/station name
- `temperature`: degrees Celsius (accepted range: -90 to 65)
- `humidity`: relative humidity percent (0 to 100)
- `rainfall`: millimetres (must be 0 or higher)

Rows with missing/unparseable required values or out-of-range measurements are rejected with row numbers and reasons in the data-quality report. No missing-value imputation is performed. Temperature placeholders such as 999 are rejected by the documented -90 to 65 °C range. Duplicate identity is the combination of observation date + normalized location: same date at different locations is allowed; an already stored date/location pair is skipped. Units are °C, mm and %. The original uploaded CSV is retained in the local `uploads/` folder; use only public, synthetic, anonymized or approved data.

## 5. Main pages and APIs
| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Dashboard and high-level metrics |
| GET, POST | `/upload` | Upload, validate and import CSV |
| GET | `/analysis` | Summary tables and Matplotlib charts |
| GET | `/records` | Latest 500 stored records |
| POST | `/records/<record_id>/delete` | Delete one stored record |
| POST | `/records/delete-all` | Delete all stored records after UI confirmation |
| GET | `/api/health` | Application/database health check |
| GET | `/api/summary` | JSON summary; optional `?location=Visakhapatnam` |

## 6. Analysis methodology
- Pandas parses dates, converts numeric fields, filters invalid rows and groups observations by calendar month.
- NumPy calculates mean, minimum, maximum and sum statistics.
- Monthly average temperature = sum of valid temperature observations in month / number of valid observations.
- Monthly total rainfall = sum of rainfall observations in month.
- Monthly average humidity = sum of humidity observations in month / number of valid observations.
- Charts: daily temperature trend, monthly rainfall totals, monthly average humidity, and temperature-versus-rainfall scatter plot. Every chart title includes the selected location(s) and observed date range; axes show units.

## 7. Database
`weather_records` is the main table. `record_id` is the primary key. Date and location indexes support common filters. SQL inserts use placeholders/parameterized queries.

## 8. Testing
Run:
```powershell
pytest -q
```
The included unit tests check empty input and summary calculations. For the project demonstration, also manually test: a valid CSV, missing required column, invalid date, missing numeric value, out-of-range humidity/rainfall/temperature, empty database, and unavailable MySQL service.

## 9. Known limitations / future improvements
- No user login, roles or forecasting.
- Duplicate detection is performed during CSV import using date + location. This is application-level protection; simultaneous concurrent imports may require a database unique constraint after cleaning existing duplicate pairs.
- Charts are regenerated from the selected dataset and currently show the combined selected records.
- For a classroom demo, use the included synthetic sample CSV or another approved dataset.
