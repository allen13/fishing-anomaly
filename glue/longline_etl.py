import sys
import boto3
import json
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, min, max, mean, stddev, count

# Get job parameters
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'input_path',
    'output_path'
])

# Initialize Spark and Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# AWS S3 client for metadata only
s3 = boto3.client('s3')

# Read CSV data from S3 using Spark
print(f"Reading data from {args['input_path']}")
df = spark.read.csv(args['input_path'], header=True, inferSchema=True)
print(f"Total records: {df.count()}")

# Drop the 'source' column if it exists
if 'source' in df.columns:
    df = df.drop('source')

# Perform aggregation by mmsi
aggregated_df = df.groupBy("mmsi").agg(
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
aggregated_df = aggregated_df.withColumn(
    "lat_range", col("max_lat") - col("min_lat")
).withColumn(
    "lon_range", col("max_lon") - col("min_lon")
).withColumn(
    "area_covered", col("lat_range") * col("lon_range")
)

vessel_count = aggregated_df.count()
print(f"After aggregation: {vessel_count} unique vessels")

# Parse S3 path
output_parts = args['output_path'].replace('s3://', '').split('/')
bucket = output_parts[0]
key_prefix = '/'.join(output_parts[1:])

# Save metadata
s3.put_object(
    Body=json.dumps({"aggregated_columns": aggregated_df.columns}, indent=2),
    Bucket=bucket,
    Key=f"{key_prefix}/columns.json"
)

# Write CSV directly to S3 using Spark
# Coalesce to ensure a single file output
csv_path = f"{args['output_path']}"
print(f"Writing {vessel_count} vessel records to {csv_path}")

# Coalesce to create a single file 
aggregated_df.coalesce(1).write.mode("overwrite").option("header", "true").csv(csv_path)

print(f"ETL complete. Data saved to {csv_path}")
job.commit() 