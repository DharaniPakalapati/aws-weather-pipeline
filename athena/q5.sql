-- Q5: average daily temperature range per city
SELECT city, AVG(temp_max_c - temp_min_c) AS avg_temp_range_c
FROM weather_db.silver_dharani_weather_silver_473469900743_ap_south_1
GROUP BY city
ORDER BY avg_temp_range_c DESC;
