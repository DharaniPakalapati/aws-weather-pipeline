-- Q3: average UV index per city, highest first
SELECT city, AVG(uv_index) AS avg_uv_index
FROM weather_db.silver_dharani_weather_silver_473469900743_ap_south_1
GROUP BY city
ORDER BY avg_uv_index DESC;
