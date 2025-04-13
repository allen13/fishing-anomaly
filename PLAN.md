# Fishing Vessel Anomaly Detection - Solution Plan

## AWS Services

### Data Storage
- **Amazon S3**: Store raw fishing vessel data, aggregated datasets, and model artifacts

### Data Processing
- **AWS Glue**: ETL service for data preprocessing and aggregation
  - ETL job for vessel data aggregation by mmsi
  - CSV output format for compatibility and simplicity

### Machine Learning
- **Amazon SageMaker**: Core ML service for anomaly detection
  - Built-in Random Cut Forest algorithm for unsupervised anomaly detection
  - CSV input format for data flexibility

### Infrastructure and Security
- **AWS IAM**: Manage access to AWS services and resources
- **Terraform**: Infrastructure as code for repeatable deployments

## Simplified Architecture

1. Raw fishing vessel data is stored in S3 (`raw/` folder)
2. AWS Glue aggregates data by vessel (mmsi) with statistics on movement patterns
3. Aggregated data is stored in S3 (`aggregated/` folder) as CSV
4. SageMaker trains Random Cut Forest model on aggregated vessel data
5. Model is deployed for real-time anomaly detection
6. All infrastructure is defined and deployed using Terraform

## Implementation Status

1. ✅ S3 bucket structure for data organization
2. ✅ Glue ETL job for vessel data aggregation (longline_etl.py)
3. ✅ SageMaker model training with Random Cut Forest
4. ✅ Terraform for infrastructure management

## Next Steps

1. Fine-tune Random Cut Forest model parameters for optimal anomaly detection
2. Evaluate model performance and adjust as needed
3. Implement a monitoring solution for ongoing data quality checks 