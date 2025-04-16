#!/usr/bin/env python3
"""
Train and Deploy Fishing Vessel Anomaly Detection Model using SageMaker RandomCutForest.

This script reads aggregated vessel-day data produced by the Glue ETL job,
trains a Random Cut Forest model, and deploys it to a SageMaker endpoint.
"""
import boto3
import sagemaker
import pandas as pd
import numpy as np
import io
import os # For path joining
import json
import argparse
import logging # Use logging for better output control
from sagemaker import RandomCutForest
from sagemaker.session import Session
from botocore.exceptions import ClientError # To catch S3 errors

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def check_s3_object_exists(s3_client, bucket, key):
    """Check if an S3 object exists using head_object."""
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        logger.info(f"Found S3 object: s3://{bucket}/{key}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            logger.warning(f"S3 object not found: s3://{bucket}/{key}")
            return False
        else:
            logger.error(f"Error checking S3 object s3://{bucket}/{key}: {e}")
            raise # Re-raise other errors

def train_and_deploy(bucket_name, instance_type_train='ml.c5.large',
                     instance_type_deploy='ml.t2.medium'):
    """
    Train a Random Cut Forest model on aggregated vessel-day data and deploy it.
    """
    logger.info(f"Starting SageMaker training process for bucket: {bucket_name}")

    # --- Configuration ---
    s3_client = boto3.client('s3')
    session = sagemaker.Session(boto_session=boto3.Session()) # Ensure session uses the same boto session
    try:
        role = sagemaker.get_execution_role()
        logger.info(f"Using SageMaker execution role: {role}")
    except Exception as e:
        logger.error(f"Error getting SageMaker execution role: {e}")
        logger.error("Ensure this script is run in an environment with appropriate SageMaker permissions (e.g., SageMaker Notebook, EC2 with role).")
        return None

    # Define S3 paths and filenames based on ETL output
    s3_prefix_aggregated = 'aggregated'
    s3_prefix_models = 'models'
    input_csv_filename = 'aggregated_vessel_days.csv'
    metadata_filename = 'columns_daily.json'
    model_info_filename = 'model_info.json'

    # Construct full S3 paths (using os.path.join handles potential trailing slashes)
    s3_input_data_path = f"s3://{bucket_name}/{os.path.join(s3_prefix_aggregated, input_csv_filename)}"
    s3_metadata_path = f"s3://{bucket_name}/{os.path.join(s3_prefix_aggregated, metadata_filename)}"
    s3_model_output_path = f"s3://{bucket_name}/{s3_prefix_models}"
    s3_model_info_path_key = os.path.join(s3_prefix_models, model_info_filename) # Key for S3 put_object

    logger.info(f"Expecting input data at: {s3_input_data_path}")
    logger.info(f"Expecting metadata at: {s3_metadata_path}")
    logger.info(f"Model artifacts will be saved to: {s3_model_output_path}")

    # --- Data Validation ---
    logger.info("Validating required input files in S3...")
    data_exists = check_s3_object_exists(s3_client, bucket_name, os.path.join(s3_prefix_aggregated, input_csv_filename))
    metadata_exists = check_s3_object_exists(s3_client, bucket_name, os.path.join(s3_prefix_aggregated, metadata_filename))

    if not data_exists:
        logger.error(f"Input data file {input_csv_filename} not found in s3://{bucket_name}/{s3_prefix_aggregated}/.")
        logger.error("Please ensure the Glue ETL job has completed successfully.")
        return None

    # --- Load Metadata (Features) ---
    aggregated_columns = []
    logger.info("Loading feature metadata...")
    if metadata_exists:
        try:
            obj = s3_client.get_object(Bucket=bucket_name, Key=os.path.join(s3_prefix_aggregated, metadata_filename))
            columns_info = json.loads(obj['Body'].read().decode('utf-8'))
            aggregated_columns = columns_info.get('aggregated_columns', [])
            if aggregated_columns:
                logger.info(f"Loaded features from {metadata_filename}: {aggregated_columns}")
            else:
                logger.warning(f"{metadata_filename} found but contains no 'aggregated_columns'. Will attempt to read from CSV.")
        except Exception as e:
            logger.warning(f"Could not load or parse {metadata_filename}: {e}. Will attempt to read from CSV header.")
            metadata_exists = False # Treat as if it doesn't exist for fallback logic

    # Fallback to reading CSV header if metadata file is missing or failed to load
    if not aggregated_columns:
        logger.info(f"Attempting to read features from CSV header: {s3_input_data_path}")
        try:
            # Read only the header row
            obj = s3_client.get_object(Bucket=bucket_name, Key=os.path.join(s3_prefix_aggregated, input_csv_filename))
            # Use pandas to easily handle CSV header reading
            metadata_df = pd.read_csv(io.BytesIO(obj['Body'].read()), nrows=0) # nrows=0 reads only header
            aggregated_columns = metadata_df.columns.tolist()
            logger.info(f"Loaded features from CSV header: {aggregated_columns}")
        except Exception as e:
            logger.error(f"Error loading features from CSV header: {e}")
            logger.error("Cannot proceed without feature information.")
            return None

    if not aggregated_columns:
         logger.error("Failed to determine feature columns. Exiting.")
         return None

    # Exclude non-feature columns (like mmsi, date identifiers if they are not features)
    # Adjust this list based on the actual output of your ETL
    columns_to_exclude = ['mmsi', 'date_float_ts', 'first_timestamp_of_day', 'last_timestamp_of_day']
    feature_columns = [col for col in aggregated_columns if col not in columns_to_exclude]

    if not feature_columns:
        logger.error(f"No feature columns remaining after excluding identifiers ({columns_to_exclude}). Check column names and ETL output.")
        return None

    logger.info(f"Using the following features for training: {feature_columns}")
    # Note: RCF typically requires features to be numeric. Ensure ETL provides numeric data.
    # The RCF estimator itself doesn't need the feature list explicitly, but it's good practice to know what's being used.

    # --- Configure RCF Estimator ---
    logger.info("Configuring RandomCutForest estimator...")
    rcf = RandomCutForest(
        role=role,
        session=session, # Pass the session
        instance_count=1,
        instance_type=instance_type_train,
        # data_location is deprecated for TrainingInput; specify in TrainingInput.s3_data
        output_path=s3_model_output_path,
        num_samples_per_tree=256, # Adjust as needed
        num_trees=100,           # Adjust as needed (increased from 50)
        eval_metrics=['accuracy', 'precision_recall_fscore'] # Note: RCF metrics might be interpreted differently (anomaly scores)
    )

    # --- Define Training Input ---
    logger.info(f"Setting up training input from: {s3_input_data_path}")
    # Using the specific CSV file as input
    training_data = sagemaker.inputs.TrainingInput(
        s3_data=s3_input_data_path,
        distribution='FullyReplicated', # Required for single CSV file on multiple instances (though we use 1 instance)
        content_type='csv',
        s3_data_type='S3Prefix', # RCF often prefers S3Prefix, even for a single file path
        input_mode='File'
    )

    # --- Train Model ---
    logger.info(f"Starting model training job (Instance type: {instance_type_train})...")
    try:
        rcf.fit({'train': training_data})
        logger.info(f"Training job {rcf.latest_training_job.job_name} completed.")
    except Exception as e:
        logger.error(f"Training job failed: {e}")
        # Consider adding logic to check job status/logs in CloudWatch here
        return None

    # --- Deploy Model ---
    logger.info(f"Deploying model to endpoint (Instance type: {instance_type_deploy})...")
    try:
        rcf_predictor = rcf.deploy(
            initial_instance_count=1,
            instance_type=instance_type_deploy,
            serializer=sagemaker.serializers.CSVSerializer(), # Specify serializer for inference input
            deserializer=sagemaker.deserializers.JSONDeserializer() # Specify deserializer for inference output
        )
        logger.info(f"Model deployed to endpoint: {rcf_predictor.endpoint_name}")
    except Exception as e:
        logger.error(f"Model deployment failed: {e}")
        return None

    # --- Save Model Information ---
    logger.info("Saving model deployment information...")
    # Use endpoint_name directly from the predictor object
    endpoint_name = rcf_predictor.endpoint_name
    # Get model name from the estimator's training job details
    model_name = rcf.latest_training_job.describe()['ModelArtifacts']['S3ModelArtifacts'].split('/')[-3] # Extract model name


    model_info = {
        'endpoint_name': endpoint_name,
        'model_name': model_name, # Use the actual trained model name
        'training_job_name': rcf.latest_training_job.job_name,
        'deployment_instance_type': instance_type_deploy,
        'feature_columns_used': feature_columns,
        'input_data_source': s3_input_data_path,
        'etl_metadata_source': s3_metadata_path if metadata_exists else "CSV Header",
    }

    try:
        s3_client.put_object(
            Body=json.dumps(model_info, indent=2),
            Bucket=bucket_name,
            Key=s3_model_info_path_key
        )
        logger.info(f"Model information saved to s3://{bucket_name}/{s3_model_info_path_key}")
    except Exception as e:
        logger.error(f"Failed to save model info to S3: {e}")

    logger.info("SageMaker training and deployment process completed successfully.")
    logger.info(f"Endpoint '{endpoint_name}' is ready for inference.")
    return model_info

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train and deploy SageMaker RandomCutForest model for Vessel Anomaly Detection')
    parser.add_argument('--bucket', type=str, required=True, help='S3 bucket name for input data and model artifacts')
    parser.add_argument('--train-instance', type=str, default='ml.m5.large', # Updated default
                        help='SageMaker instance type for training job')
    parser.add_argument('--deploy-instance', type=str, default='ml.t2.medium',
                        help='SageMaker instance type for deployment endpoint')

    args = parser.parse_args()

    train_and_deploy(
        bucket_name=args.bucket,
        instance_type_train=args.train_instance,
        instance_type_deploy=args.deploy_instance
    ) 