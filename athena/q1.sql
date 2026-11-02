-- Q1: hottest city on the most recent ingestion date
SELECT city, temp_max_c
FROM weather_db.silver_dharani_weather_silver_473469900743_ap_south_1
WHERE ingestion_date = (
  SELECT max(ingestion_date)
  FROM weather_db.silver_dharani_weather_silver_473469900743_ap_south_1
)
ORDER BY temp_max_c DESC
LIMIT 1;
