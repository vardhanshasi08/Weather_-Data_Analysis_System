import pandas as pd
from analysis.weather_analysis import build_summary

def test_build_summary_empty():
    result = build_summary(pd.DataFrame())
    assert result["total_records"] == 0
    assert result["monthly"] == []

def test_build_summary_values():
    df = pd.DataFrame({
        "observation_date": pd.to_datetime(["2026-01-01", "2026-01-02"]),
        "location": ["Vizag", "Vizag"],
        "temperature": [20.0, 30.0],
        "humidity": [50.0, 70.0],
        "rainfall": [2.0, 3.0],
    })
    result = build_summary(df)
    assert result["total_records"] == 2
    assert result["average_temperature"] == 25.0
    assert result["total_rainfall"] == 5.0

def test_csv_validation_reports_bad_rows(tmp_path):
    from analysis.weather_analysis import validate_weather_csv
    csv_path = tmp_path / "quality.csv"
    csv_path.write_text(
        "date,location,temperature,humidity,rainfall\n"
        "2025-01-01,Vizag,28,70,2\n"
        "2025-01-02,Vizag,999,60,0\n"
        "2025-01-03,Vizag,25,,1\n",
        encoding="utf-8",
    )
    valid, report = validate_weather_csv(csv_path)
    assert len(valid) == 1
    assert report["rejected_rows"] == 2
    assert report["out_of_range_rows"] == 1
    assert len(report["rejected_details"]) == 2
