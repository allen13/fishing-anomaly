#!/usr/bin/env python3
"""
Fishing Vessel Anomaly Detection using SageMaker RandomCutForest
"""
import boto3
import sagemaker
import pandas as pd
import numpy as np
import io
import os
import json
import argparse
from sagemaker import RandomCutForest
from sagemaker.session import Session

def train_and_deploy(bucket_name, instance_type_train='ml.c5.large', 
                     instance_type_deploy='ml.t2.medium'):
    """
    Train a Random Cut Forest model and deploy it
    """
    print(f"Setting up SageMaker training for bucket: {bucket_name}")
    
    # Set up SageMaker session
    session = sagemaker.Session()
    role = sagemaker.get_execution_role()
    
    # Confirm access to S3 bucket
    s3_client = boto3.client('s3')
    
    # Check for aggregated CSV data
    data_prefix = 'aggregated'
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=f'{data_prefix}/', MaxKeys=10)
        print("Files available:")
        for obj in response.get('Contents', []):
            print(f"- {obj['Key']}")
            
        # Specifically check for the aggregated data CSV file
        has_aggregated_data = False
        data_key = None
        for obj in response.get('Contents', []):
            if obj['Key'].endswith('aggregated_data.csv'):
                has_aggregated_data = True
                data_key = obj['Key']
                print(f"Found aggregated CSV data file: {data_key}")
                
        if not has_aggregated_data:
            print("Warning: aggregated_data.csv not found. Will proceed with available data.")
            
    except Exception as e:
        print(f"Error accessing data: {e}")
        print("Make sure the Glue job has completed and created the CSV files.")
        return None
    
    # Load metadata and inspect the aggregated data
    try:
        # Load the columns.json file which contains aggregated column information
        try:
            obj = s3_client.get_object(Bucket=bucket_name, Key=f'{data_prefix}/columns.json')
            columns_info = json.loads(obj['Body'].read().decode('utf-8'))
            aggregated_columns = columns_info.get('aggregated_columns', [])
            print(f"Aggregated columns available: {aggregated_columns}")
        except Exception as e:
            print(f"Could not load columns.json, will try CSV file directly: {e}")
            
            # Try the CSV file directly
            try:
                if data_key:
                    obj = s3_client.get_object(Bucket=bucket_name, Key=data_key)
                    metadata_df = pd.read_csv(io.BytesIO(obj['Body'].read()), nrows=1)
                    aggregated_columns = metadata_df.columns.tolist()
                    print(f"Loaded columns from CSV: {aggregated_columns}")
                else:
                    raise ValueError("No aggregated data CSV found")
            except Exception as e2:
                print(f"Error loading CSV file: {e2}")
                aggregated_columns = []
        
        if aggregated_columns:
            print("These aggregated vessel metrics will be used for anomaly detection.")
        else:
            print("Warning: No column information found. Model will use all available features.")
    except Exception as e:
        print(f"Error loading metadata: {e}")
        print("This is expected if the Glue job hasn't completed yet.")
        return None
    
    # Create Amazon SageMaker RandomCutForest model
    # The model will use all aggregated vessel metrics for anomaly detection
    rcf = RandomCutForest(
        role=role,
        instance_count=1,
        instance_type=instance_type_train,
        data_location=f"s3://{bucket_name}/{data_prefix}",
        output_path=f"s3://{bucket_name}/models",
        num_samples_per_tree=256,
        num_trees=50,
        eval_metrics=['accuracy', 'precision_recall_fscore']
    )
    
    # Define training input configuration
    s3_input_path = f"s3://{bucket_name}/{data_key}" if data_key else f"s3://{bucket_name}/{data_prefix}"
    
    training_data = sagemaker.inputs.TrainingInput(
        s3_data=s3_input_path,
        content_type='text/csv',  # Using CSV format instead of RecordIO
        s3_data_type='S3Object' if data_key else 'S3Prefix',
        input_mode='File'  # Using File mode instead of Pipe mode since we're using CSV
    )
    
    # Start training job
    print("Starting model training on aggregated vessel data...")
    rcf.fit({'train': training_data})
    
    # Deploy the model to an endpoint
    print(f"Deploying model to endpoint using instance type: {instance_type_deploy}")
    rcf_predictor = rcf.deploy(
        initial_instance_count=1,
        instance_type=instance_type_deploy
    )
    
    # Save information about the model and features used
    model_info = {
        'endpoint_name': rcf_predictor.endpoint_name,
        'model_name': rcf.model_name,
        'creation_time': rcf_predictor._endpoint_config_name,
        'aggregated_features': aggregated_columns,
        'data_source': s3_input_path
    }
    
    # Save model info to S3
    s3_client.put_object(
        Body=json.dumps(model_info, indent=2),
        Bucket=bucket_name,
        Key='models/model_info.json'
    )
    
    print(f"Model information saved to s3://{bucket_name}/models/model_info.json")
    print("This model is trained to detect anomalies in vessel movement patterns based on aggregated metrics per vessel.")
    return model_info

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train and deploy SageMaker RandomCutForest model')
    parser.add_argument('--bucket', type=str, required=True, help='S3 bucket name')
    parser.add_argument('--train-instance', type=str, default='ml.c5.large', 
                        help='SageMaker training instance type')
    parser.add_argument('--deploy-instance', type=str, default='ml.t2.medium', 
                        help='SageMaker deployment instance type')
    
    args = parser.parse_args()
    
    train_and_deploy(
        bucket_name=args.bucket,
        instance_type_train=args.train_instance,
        instance_type_deploy=args.deploy_instance
    ) 