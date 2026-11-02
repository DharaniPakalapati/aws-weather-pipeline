import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F

args = getResolvedOptions(sys.argv, ["JOB_NAME", "BRONZE_PATH", "SILVER_PATH"])
sc = SparkContext()
glue = GlueContext(sc)
spark = glue.spark_session
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
job = Job(glue)
job.init(args["JOB_NAME"], args)

df = spark.read.json(args["BRONZE_PATH"] + "ingestion_date=*/*.json")

zipped = df.select(
    "city", "ingestion_date", "latitude", "longitude",
    F.arrays_zip(
        F.col("daily.time").alias("time"),
        F.col("daily.temperature_2m_max").alias("tmax"),
        F.col("daily.temperature_2m_min").alias("tmin"),
        F.col("daily.precipitation_sum").alias("precip"),
        F.col("daily.wind_speed_10m_max").alias("wind"),
        F.col("daily.uv_index_max").alias("uv"),
    ).alias("z"),
)

out = (zipped
    .select("city", "ingestion_date", "latitude", "longitude", F.explode("z").alias("d"))
    .select(
        "city",
        F.col("latitude").cast("double"),
        F.col("longitude").cast("double"),
        F.col("d.time").alias("forecast_date"),
        F.col("d.tmax").cast("double").alias("temp_max_c"),
        F.col("d.tmin").cast("double").alias("temp_min_c"),
        F.col("d.precip").cast("double").alias("precipitation_mm"),
        F.col("d.wind").cast("double").alias("windspeed_kmh"),
        F.col("d.uv").cast("double").alias("uv_index"),
        "ingestion_date",
    ))

out.write.mode("overwrite").partitionBy("ingestion_date").parquet(args["SILVER_PATH"])
job.commit()
