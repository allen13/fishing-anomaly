import sys
import boto3
import json
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, min, max, mean, stddev, count, to_date
import logging

# Set up logging for AWS Glue environment
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get job parameters
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'input_path',
    'output_path'
])

# Extract path parameters with clear names and examples
job_name = args['JOB_NAME']                       # Example: 'longline-vessel-etl'
raw_data_path = args['input_path']                # Example: 's3://fishing-anomaly-detection-1744553260/raw/'
output_base_path = args['output_path']            # Example: 's3://fishing-anomaly-detection-1744553260/aggregated/'

# Parse S3 bucket and key components
s3_parts = output_base_path.replace('s3://', '').split('/', 1)
s3_bucket = s3_parts[0]                           # Example: 'fishing-anomaly-detection-1744553260'
s3_prefix = s3_parts[1] if len(s3_parts) > 1 else ''  # Example: 'aggregated/'

# Define output filenames and paths
metadata_file = f"{s3_prefix}columns_daily.json"        # Example: 'aggregated/columns_daily.json'
temp_folder = f"{s3_prefix}temp_dir/"             # Example: 'aggregated/temp_dir/'
final_output_file = f"{s3_prefix}aggregated_vessel_days.csv"  # Example: 'aggregated/aggregated_vessel_days.csv'
temp_success_file = f"{temp_folder}_SUCCESS"      # Example: 'aggregated/temp_dir/_SUCCESS'

# Initialize Spark and Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(job_name, args)

# Log job parameters for clarity
logger.info(f"Starting job: {job_name}")
logger.info(f"Input data path: {raw_data_path}")
logger.info(f"Output base path: {output_base_path}")
logger.info(f"S3 bucket: {s3_bucket}")
logger.info(f"S3 prefix: {s3_prefix}")
logger.info(f"Final output file will be: s3://{s3_bucket}/{final_output_file}")

# AWS S3 client for metadata operations
s3 = boto3.client('s3')

# Read CSV data from S3 using Spark
logger.info(f"Reading data from {raw_data_path}")
df = spark.read.csv(raw_data_path, header=True, inferSchema=True)
record_count = df.count()
logger.info(f"Total records: {record_count}")

# Drop the 'source' column if it exists
if 'source' in df.columns:
    logger.info("Dropping 'source' column")
    df = df.drop('source')

# Extract date from timestamp
logger.info("Extracting date from timestamp")
df = df.withColumn("date", to_date(col("timestamp")))

# Perform aggregation by mmsi and date
logger.info("Starting aggregation by vessel MMSI and date")
aggregated_df = df.groupBy("mmsi", "date").agg(
    # Time-based metrics
    min("timestamp").alias("first_timestamp"),
    max("timestamp").alias("last_timestamp"),
    (max("timestamp") - min("timestamp")).alias("time_span"),
    
    # Count of positions
    count("mmsi").alias("position_count"),
    
    # Speed statistics
    mean("speed").alias("avg_speed"),
    stddev("speed").alias("speed_std"),
    min("speed").alias("min_speed"),
    max("speed").alias("max_speed"),
    
    # Course statistics
    mean("course").alias("avg_course"),
    stddev("course").alias("course_std"),
    (max("course") - min("course")).alias("course_range"),
    
    # Distance metrics
    mean("distance_from_shore").alias("avg_distance_from_shore"),
    mean("distance_from_port").alias("avg_distance_from_port"),
    
    # Fishing activity (if available)
    mean("is_fishing").alias("avg_fishing_indicator"),
    
    # Position statistics
    mean("lat").alias("avg_lat"),
    mean("lon").alias("avg_lon"),
    min("lat").alias("min_lat"),
    max("lat").alias("max_lat"),
    min("lon").alias("min_lon"),
    max("lon").alias("max_lon")
)

# Calculate area covered
logger.info("Calculating area coverage metrics")
aggregated_df = aggregated_df.withColumn(
    "lat_range", col("max_lat") - col("min_lat")
).withColumn(
    "lon_range", col("max_lon") - col("min_lon")
).withColumn(
    "area_covered", col("lat_range") * col("lon_range")
)

vessel_day_count = aggregated_df.count()
logger.info(f"After aggregation: {vessel_day_count} unique vessel-day records")

# Save metadata about columns
logger.info("Saving column metadata")
try:
    s3.put_object(
        Body=json.dumps({"aggregated_columns": aggregated_df.columns}, indent=2),
        Bucket=s3_bucket,
        Key=metadata_file
    )
    logger.info(f"Metadata saved to s3://{s3_bucket}/{metadata_file}")
except Exception as e:
    logger.error(f"Error saving metadata: {str(e)}")

# Write aggregated data to CSV with a specific filename
logger.info(f"Writing {vessel_day_count} vessel-day records")

try:
    # Step 1: Write to temporary location using Spark
    temp_s3_path = f"s3://{s3_bucket}/{temp_folder}"
    logger.info(f"Writing data to temporary location: {temp_s3_path}")
    aggregated_df.coalesce(1).write.mode("overwrite").option("header", "true").csv(temp_s3_path)
    
    # Step 2: Find the CSV file in the temporary location
    temp_csv_files = []
    response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=temp_folder)
    if 'Contents' in response:
        temp_csv_files = [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.csv')]
    
    if not temp_csv_files:
        raise Exception("No CSV file was created in temporary directory")
    
    # Step 3: Get the source CSV file (should be just one due to coalesce)
    temp_csv_file = temp_csv_files[0]
    logger.info(f"Found temporary CSV file: {temp_csv_file}")
    
    # Step 4: Copy to final destination with clean name
    logger.info(f"Renaming to final output file: s3://{s3_bucket}/{final_output_file}")
    s3.copy_object(
        Bucket=s3_bucket,
        CopySource={'Bucket': s3_bucket, 'Key': temp_csv_file},
        Key=final_output_file
    )
    
    # Step 5: Clean up temporary files
    logger.info("Cleaning up temporary files")
    for key in temp_csv_files:
        s3.delete_object(Bucket=s3_bucket, Key=key)
    
    # Step 6: Delete _SUCCESS file if it exists
    try:
        s3.delete_object(Bucket=s3_bucket, Key=temp_success_file)
    except Exception:
        pass  # Ignore if _SUCCESS file doesn't exist
    
    logger.info(f"Data successfully written to s3://{s3_bucket}/{final_output_file}")
except Exception as e:
    logger.error(f"Error in write process: {str(e)}")
    raise

logger.info(f"ETL job complete")
job.commit() 