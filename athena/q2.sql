-- Q2: total rainfall per city across all dates
SELECT city, SUM(precipitation_mm) AS total_rain_mm
FROM weather_db.silver_dharani_weather_silver_473469900743_ap_south_1
GROUP BY city
ORDER BY total_rain_mm DESC;
