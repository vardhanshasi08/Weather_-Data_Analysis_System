# Data Dictionary

| Field | Type | Meaning | Unit / constraint |
|---|---|---|---|
| record_id | BIGINT | Unique observation identifier | Primary key, auto-increment |
| observation_date | DATE | Date of observation | Required |
| location | VARCHAR(120) | City/station name | Required |
| temperature | DECIMAL(5,2) | Recorded air temperature | °C; -90 to 65 |
| humidity | DECIMAL(5,2) | Relative humidity | %; 0 to 100 |
| rainfall | DECIMAL(7,2) | Recorded rainfall | mm; >= 0 |
| created_at | TIMESTAMP | Time record was inserted | Database generated |

## Relationship / ER sketch
`weather_records` is a standalone observation table in this version. Each row represents one measurement for one location on one date. A future multi-table design could separate `locations` and reference it using a foreign key.


## Measurement units and validation policy
- temperature: degrees Celsius (°C), accepted range -90 to 65.
- humidity: relative humidity percentage (%), accepted range 0 to 100.
- rainfall: millimetres (mm), must be non-negative.
- observation_date: calendar date (YYYY-MM-DD).
- location: city/station name; same date is allowed for different locations.

Missing or non-numeric required values are rejected (no automatic filling). Out-of-range values are rejected and row-level reasons are shown in the upload data-quality report. Duplicate key for import is (observation_date, normalized location).
