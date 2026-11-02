USE weather_analysis;

-- 1) Review duplicates before deletion
SELECT observation_date, location, COUNT(*) AS duplicate_count
FROM weather_records
GROUP BY observation_date, location
HAVING COUNT(*) > 1;

-- 2) Keep the earliest record_id and remove later duplicates
DELETE w1 FROM weather_records w1
JOIN weather_records w2
  ON w1.observation_date = w2.observation_date
 AND w1.location = w2.location
 AND w1.record_id > w2.record_id;

-- 3) Add database-level duplicate protection
ALTER TABLE weather_records
ADD CONSTRAINT uq_weather_date_location UNIQUE (observation_date, location);

-- 4) Verify
SELECT COUNT(*) AS total_records FROM weather_records;
