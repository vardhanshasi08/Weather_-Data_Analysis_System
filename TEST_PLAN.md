# Test Plan

| ID | Scenario | Expected result |
|---|---|---|
| T01 | Open dashboard with empty database | Dashboard loads and shows zero records |
| T02 | Upload valid sample CSV | Valid rows inserted and success message shown |
| T03 | Upload non-CSV file | Upload rejected |
| T04 | Submit without selecting a file | Validation message shown |
| T05 | CSV missing a required column | Clear missing-column error |
| T06 | CSV contains invalid date | Row rejected and counted |
| T07 | Humidity outside 0–100 | Row rejected and counted |
| T08 | Negative rainfall | Row rejected and counted |
| T09 | Empty database analysis | Empty-state message shown |
| T10 | MySQL unavailable | Health API reports database disconnected |
| T11 | View records after import | Inserted rows appear in records table |
| T12 | Open analysis after import | Metrics, monthly table and charts appear |

Run automated unit tests with `pytest -q`. Record actual pass/fail results during the team's local run; do not claim unexecuted manual tests passed.


## Additional acceptance tests
1. Upload a row with missing humidity/rainfall: row is rejected and reason appears in the data-quality report.
2. Upload temperature 999, -150, text, humidity >100, or negative rainfall: each affected row is rejected and explained.
3. Upload same date for two different locations: both are accepted.
4. Upload same date + same location again: duplicate is skipped and counted.
5. Confirm every chart title includes location(s) and observed date range; axes include °C, mm, or %.
