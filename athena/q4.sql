-- Q4: days per city with wind speed above 50 km/h
SELECT city, COUNT(*) AS windy_days
FROM weather_db.silver_dharani_weather_silver_473469900743_ap_south_1
WHERE windspeed_kmh > 50
GROUP BY city
ORDER BY windy_days DESC;
