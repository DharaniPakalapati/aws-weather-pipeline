# AWS Weather Data Pipeline

A serverless, fully automated data pipeline on AWS that ingests daily weather data for 10 global hub cities, stores it in a Bronze/Silver data lake on S3, transforms it with PySpark, and makes it queryable with SQL in Athena. All infrastructure is defined in a single CloudFormation template.

## Business problem

A travel technology company operates flight search and booking across 10 major international hubs. Weather disruptions (storms, high winds, extreme heat) are a top driver of complaints and refunds, but there is no centralised, queryable weather history. This pipeline builds that dataset so the operations team can correlate weather with booking and delay patterns and surface weather-risk scores in dashboards.

## Architecture

```
EventBridge (daily 6am UTC)
   -> Lambda (calls Open-Meteo API, 10 cities)
   -> S3 Bronze (raw JSON, ingestion_date=YYYY-MM-DD/city.json)
   -> Glue Crawler (registers Bronze table)
   -> Glue ETL Job (PySpark: arrays_zip + explode, JSON -> Parquet)
   -> S3 Silver (Parquet, partitioned by ingestion_date)
   -> Glue Crawler (registers Silver table)
   -> Athena (SQL analysis)
```

| Layer | Purpose |
|---|---|
| Bronze | Raw API response, unchanged. Lets us replay the ETL without re-calling the API. |
| Silver | Clean, flattened, columnar Parquet. One row per city per forecast day. |

## Tech stack

AWS Lambda, EventBridge, S3, Glue (Crawlers and PySpark ETL), Athena, IAM, CloudFormation. Data source: Open-Meteo API (free, no key).

## Repository layout

```
infra/template.yaml        CloudFormation template (all resources)
glue/bronze_to_silver.py   PySpark ETL job
athena/q1.sql ... q5.sql   Analysis queries
docs/screenshots/          Evidence of the working pipeline
```

## Deploy with one command

```bash
aws cloudformation deploy \
  --template-file infra/template.yaml \
  --stack-name weather-pipeline \
  --capabilities CAPABILITY_IAM \
  --region ap-south-1 \
  --parameter-overrides Prefix=<your-prefix>
```

Then upload the Glue script (the bucket name appears in the stack outputs):

```bash
aws s3 cp glue/bronze_to_silver.py \
  s3://<prefix>-weather-artifacts-<ACCOUNT_ID>-ap-south-1/scripts/bronze_to_silver.py
```

## Run the pipeline

```bash
aws lambda invoke --function-name <prefix>-weather-ingest --region ap-south-1 out.json
aws glue start-crawler --name <prefix>-weather-bronze-crawler --region ap-south-1
aws glue start-job-run --job-name <prefix>-weather-bronze-to-silver --region ap-south-1
aws glue start-crawler --name <prefix>-weather-silver-crawler --region ap-south-1
```

After the first manual run, EventBridge triggers the ingestion Lambda daily at 6am UTC.

## Silver schema

| Column | Type |
|---|---|
| city | string |
| latitude, longitude | double |
| forecast_date | string |
| temp_max_c, temp_min_c | double |
| precipitation_mm | double |
| windspeed_kmh | double |
| uv_index | double |
| ingestion_date (partition) | string |

## Athena queries

Saved in `athena/`. Replace the table name with your Silver table.

1. `q1.sql` Hottest city on the most recent ingestion date
2. `q2.sql` Total rainfall per city
3. `q3.sql` Average UV index per city
4. `q4.sql` Days per city with wind above 50 km/h
5. `q5.sql` Average daily temperature range per city

## Screenshots

| Evidence | File |
|---|---|
| Bronze bucket (10 JSON files) | `docs/screenshots/s3-bronze.png` |
| Silver bucket (Parquet partitions) | `docs/screenshots/s3-silver.png` |
| Glue tables in weather_db | `docs/screenshots/glue-tables.png` |
| ETL job run (succeeded) | `docs/screenshots/glue-job-run.png` |
| Lambda test result | `docs/screenshots/lambda-test.png` |
| EventBridge schedule and target | `docs/screenshots/eventbridge-rule.png` |
| Athena Q1 to Q5 | `docs/screenshots/athena-q1.png` ... `athena-q5.png` |

## Design decisions

- **Bronze/Silver separation:** raw data is kept so the transform is always replayable.
- **Parquet:** columnar and compressed, so Athena scans only the columns queried.
- **Partitioning by ingestion_date:** enables partition pruning and keeps each day isolated.
- **Lambda uses urllib instead of requests:** avoids packaging a Lambda Layer, so the whole stack deploys with one command.
- **Least privilege:** the Lambda role can only write objects to the Bronze bucket.
- **Serverless:** no EC2 and no idle compute, so near-zero running cost.

## Scaling to 500 cities

Fan out API calls with SQS and multiple Lambda workers to avoid timeouts. The Glue job is Spark, so it scales with more workers. The S3 partition layout already isolates each day.

## Possible next steps

Step Functions orchestration (crawl, ETL, crawl without manual steps), CloudWatch alarms with SNS alerts, data quality checks, and GitHub Actions CI/CD with OIDC.

## Cleanup

Empty the three buckets first (CloudFormation cannot delete non-empty buckets), then delete the stack:

```bash
aws s3 rm s3://<bronze-bucket> --recursive
aws s3 rm s3://<silver-bucket> --recursive
aws s3 rm s3://<artifacts-bucket> --recursive
aws cloudformation delete-stack --stack-name weather-pipeline --region ap-south-1
```

## Resume bullets

- Built a serverless weather data pipeline on AWS for a travel operations use case, ingesting daily forecast data for 10 global hub cities using Lambda, S3, Glue ETL, and Athena.
- Designed a Bronze/Silver data lake on S3 with Hive-style partitioning, enabling Athena partition pruning on analytical queries.
- Authored a PySpark Glue ETL job to flatten nested JSON arrays from the Open-Meteo API into a partitioned Parquet dataset for delay-risk analysis.
- Defined the entire stack in a single CloudFormation template and automated daily ingestion via EventBridge, with no persistent compute resources.
