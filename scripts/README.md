# Scripts

This directory contains utility scripts for the fishing vessel anomaly detection project.

## ETL Job Trigger Script

The `trigger_etl.py` script allows you to manually trigger the AWS Glue ETL job that processes fishing vessel data.

### Prerequisites

- Python 3.6+
- AWS credentials configured (via AWS CLI, environment variables, or instance profile)
- Required Python packages: `boto3`

You can install the required packages with:

```bash
pip install boto3
```

### Usage

Basic usage:

```bash
python trigger_etl.py
```

This will trigger the default ETL job (`longline-vessel-etl`) and return immediately.

The script is configured with hardcoded S3 paths:
- Input path: `s3://fishing-anomaly-detection-1744553260/raw/`
- Output path: `s3://fishing-anomaly-detection-1744553260/aggregated/`

The ETL job will:
1. Read vessel data from the input path
2. Process and aggregate the data by vessel MMSI
3. Output a clean CSV file named `aggregated_vessels.csv` in the output path

### Options

- `--job-name`: Specify a different job name (default: `longline-vessel-etl`)
- `--region`: Specify the AWS region (default: `us-east-1`)
- `--wait`: Wait for the job to complete and show status updates
- `--log-level`: Set the logging level (choices: DEBUG, INFO, WARNING, ERROR, CRITICAL, default: INFO)

### Examples

Trigger the job and wait for completion:

```bash
python trigger_etl.py --wait
```

Specify a different job name and region:

```bash
python trigger_etl.py --job-name custom-etl-job --region us-west-2
```

Enable debug logging for more detailed output:

```bash
python trigger_etl.py --wait --log-level DEBUG
```

### Logging

The script uses Python's standard logging module with the following features:

- Timestamped log entries
- Log level indication ([INFO], [ERROR], etc.)
- Different logging levels for filtering output verbosity
- Better integration with log aggregation tools

### Troubleshooting

If you encounter errors:

1. Ensure your AWS credentials are properly configured
2. Verify the job name exists in your AWS account
3. Check you have the necessary IAM permissions to start Glue jobs
4. Use `--log-level DEBUG` for more detailed diagnostic information 