import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REQUIRED = ["date", "location", "temperature", "humidity", "rainfall"]

def validate_weather_csv(path):
    """Return valid rows and an auditable row-level data-quality report.

    Missing required measurements are rejected (not silently imputed).
    Temperature is accepted from -90 to 65 °C, humidity from 0 to 100%,
    and rainfall must be >= 0 mm.
    """
    raw = pd.read_csv(path)
    raw.columns = [str(c).strip().lower() for c in raw.columns]
    missing_cols = [c for c in REQUIRED if c not in raw.columns]
    if missing_cols:
        raise ValueError("Missing required columns: " + ", ".join(missing_cols))
    df = raw[REQUIRED].copy()
    df.insert(0, "source_row", range(2, len(df) + 2))  # header is row 1
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["temperature", "humidity", "rainfall"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["location"] = df["location"].astype("string").str.strip()

    reasons = [[] for _ in range(len(df))]
    def mark(mask, message):
        for idx in df.index[mask.fillna(False)]:
            reasons[idx].append(message)

    mark(df["date"].isna(), "Missing or invalid date")
    mark(df["location"].isna() | (df["location"] == ""), "Missing location")
    for col, label in [("temperature", "temperature"), ("humidity", "humidity"), ("rainfall", "rainfall")]:
        mark(df[col].isna(), f"Missing or non-numeric {label}")
    mark(df["temperature"].notna() & ~df["temperature"].between(-90, 65), "Temperature outside -90 to 65 °C")
    mark(df["humidity"].notna() & ~df["humidity"].between(0, 100), "Humidity outside 0 to 100%")
    mark(df["rainfall"].notna() & (df["rainfall"] < 0), "Rainfall below 0 mm")

    df["rejection_reason"] = ["; ".join(r) for r in reasons]
    rejected = df[df["rejection_reason"] != ""].copy()
    clean = df[df["rejection_reason"] == ""].drop(columns=["rejection_reason"]).copy()
    clean = clean.rename(columns={"date": "observation_date"})
    quality = {
        "total_rows": int(len(df)), "valid_rows": int(len(clean)),
        "rejected_rows": int(len(rejected)),
        "invalid_dates": int(df["date"].isna().sum()),
        "missing_locations": int((df["location"].isna() | (df["location"] == "")).sum()),
        "missing_or_non_numeric_measurements": int(df[["temperature", "humidity", "rainfall"]].isna().any(axis=1).sum()),
        "out_of_range_rows": int(sum(any(x in reason for x in ["outside", "below"]) for reason in rejected["rejection_reason"])),
        "rejected_details": [{"row": int(r.source_row), "reason": r.rejection_reason} for r in rejected.itertuples()],
        "policy": "Rows with missing/invalid required fields are rejected; no imputation is applied."
    }
    return clean, quality

def build_summary(df):
    if df.empty:
        return {"total_records": 0, "average_temperature": None, "minimum_temperature": None,
                "maximum_temperature": None, "average_humidity": None, "total_rainfall": 0,
                "monthly": []}
    df = df.copy()
    df["observation_date"] = pd.to_datetime(df["observation_date"])
    monthly = df.assign(month=df["observation_date"].dt.to_period("M").astype(str)).groupby("month").agg(
        avg_temperature=("temperature", "mean"),
        min_temperature=("temperature", "min"),
        max_temperature=("temperature", "max"),
        avg_humidity=("humidity", "mean"),
        total_rainfall=("rainfall", "sum"),
        records=("temperature", "count")
    ).reset_index()
    return {
        "total_records": int(len(df)),
        "average_temperature": round(float(np.mean(df["temperature"])), 2),
        "minimum_temperature": round(float(np.min(df["temperature"])), 2),
        "maximum_temperature": round(float(np.max(df["temperature"])), 2),
        "average_humidity": round(float(np.mean(df["humidity"])), 2),
        "total_rainfall": round(float(np.sum(df["rainfall"])), 2),
        "monthly": [{k: (round(float(v), 2) if isinstance(v, (float, np.floating)) else (int(v) if isinstance(v, (np.integer,)) else v))
                     for k, v in row.items()} for row in monthly.to_dict(orient="records")]
    }

def create_charts(df, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    data = df.copy()
    data["observation_date"] = pd.to_datetime(data["observation_date"])
    start = data["observation_date"].min().strftime("%d %b %Y")
    end = data["observation_date"].max().strftime("%d %b %Y")
    locations = sorted(data["location"].dropna().astype(str).unique()) if "location" in data else []
    place = locations[0] if len(locations) == 1 else f"All locations ({len(locations)})"
    period = f"{start} to {end}"
    monthly = data.assign(month=data["observation_date"].dt.to_period("M").astype(str)).groupby("month").agg(
        avg_temp=("temperature", "mean"), rainfall=("rainfall", "sum"), humidity=("humidity", "mean")
    ).reset_index()
    charts = [
        ("temperature_trend.png", lambda: plt.plot(data["observation_date"], data["temperature"], marker="o", linewidth=1.8, label="Temperature"), "Temperature trend", "Date", "Temperature (°C)"),
        ("monthly_rainfall.png", lambda: plt.bar(monthly["month"], monthly["rainfall"], label="Rainfall"), "Monthly rainfall", "Month", "Rainfall (mm)"),
        ("monthly_humidity.png", lambda: plt.plot(monthly["month"], monthly["humidity"], marker="o", label="Average humidity"), "Monthly average humidity", "Month", "Humidity (%)"),
        ("temperature_rainfall.png", lambda: plt.scatter(data["temperature"], data["rainfall"], alpha=.7, label="Daily observations"), "Temperature vs rainfall", "Temperature (°C)", "Rainfall (mm)")
    ]
    for filename, draw, title, xlabel, ylabel in charts:
        plt.figure(figsize=(9, 4.5)); draw()
        plt.title(f"{title} — {place}\n{period}")
        plt.xlabel(xlabel); plt.ylabel(ylabel); plt.grid(alpha=.25); plt.legend()
        if "monthly" in filename: plt.xticks(rotation=35)
        plt.tight_layout(); plt.savefig(os.path.join(output_dir, filename), dpi=140); plt.close()
