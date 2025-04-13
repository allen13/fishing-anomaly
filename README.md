# Fishing Vessel Anomaly Detection

This project implements an anomaly detection solution for identifying unusual patterns in fishing vessel movements using AWS services and Terraform.

## Overview

The solution analyzes vessel movement data (positions, speeds, courses) to identify vessels exhibiting anomalous behavior patterns. It uses Random Cut Forest, an unsupervised machine learning algorithm, to detect outliers in aggregated vessel metrics.

## Architecture

1. **Data Storage**: Raw vessel tracking data stored in S3
2. **Data Processing**: AWS Glue ETL job aggregates data by vessel (mmsi)
3. **Machine Learning**: Amazon SageMaker trains and hosts Random Cut Forest model
4. **Deployment**: All infrastructure managed with Terraform

## Data

The project uses AIS (Automatic Identification System) fishing vessel data from Global Fishing Watch. For detailed information about the dataset, see [DATA.md](DATA.md).

## Setup

1. **Clone this repository**

2. **Apply Terraform configuration**
   ```bash
   cd terraform
   terraform init
   terraform apply
   ```

3. **Upload vessel data to S3**
   ```bash
   # Upload data to the raw/ folder in the S3 bucket
   aws s3 cp drifting_longlines.csv s3://fishing-anomaly-detection-1744553260/raw/
   ```

## Components

- **S3 Bucket**: Stores raw data and processed results
- **Glue ETL Job**: Aggregates vessel data by mmsi
- **SageMaker**: Trains Random Cut Forest model on aggregated data

## Project Structure

```
.
├── DATA.md                       # Dataset information
├── README.md                     # This file
├── glue/
│   └── longline_etl.py           # Vessel data aggregation script
└── terraform/                    # Infrastructure as code
    ├── glue.tf                   # AWS Glue resources
    ├── main.tf                   # Core infrastructure
    ├── outputs.tf                # Output values
    ├── scripts/                  # SageMaker training scripts
    └── variables.tf              # Configuration variables
``` 