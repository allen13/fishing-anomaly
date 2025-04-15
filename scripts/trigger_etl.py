#!/usr/bin/env python3
"""
Script to manually trigger the AWS Glue ETL job for vessel data aggregation.
"""
import boto3
import argparse
import time
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('glue_trigger')

def trigger_glue_job(job_name, wait=False, region="us-east-1"):
    """
    Trigger the AWS Glue ETL job and optionally wait for it to complete.
    
    Args:
        job_name (str): Name of the Glue job to trigger
        wait (bool): Whether to wait for the job to complete
        region (str): AWS region where the job is located
    
    Returns:
        str: The job run ID
    """
    logger.info(f"Connecting to AWS Glue in {region}...")
    glue_client = boto3.client('glue', region_name=region)
    
    # Start the job run
    logger.info(f"Starting Glue job: {job_name}")
    response = glue_client.start_job_run(
        JobName=job_name,
        Arguments={
           '--input_path': 's3://fishing-anomaly-detection-1744553260/raw/',
           '--output_path': 's3://fishing-anomaly-detection-1744553260/aggregated/'
        }
    )
    
    job_run_id = response['JobRunId']
    logger.info(f"Job started with run ID: {job_run_id}")
    
    if not wait:
        logger.info("Job started. Not waiting for completion.")
        return job_run_id
    
    # Wait for the job to complete if requested
    logger.info("Waiting for job to complete...")
    
    while True:
        run_response = glue_client.get_job_run(
            JobName=job_name,
            RunId=job_run_id
        )
        
        status = run_response['JobRun']['JobRunState']
        logger.info(f"Current status: {status}")
        
        if status in ['SUCCEEDED', 'FAILED', 'ERROR', 'TIMEOUT', 'STOPPED']:
            if status == 'SUCCEEDED':
                logger.info(f"Job completed successfully in {run_response['JobRun']['ExecutionTime']/1000} seconds")
            else:
                error_message = run_response['JobRun'].get('ErrorMessage', 'No error message provided')
                logger.error(f"Job ended with status {status}: {error_message}")
            
            break
        
        # Wait for 30 seconds before checking again
        time.sleep(30)
    
    return job_run_id

def main():
    parser = argparse.ArgumentParser(description='Trigger AWS Glue ETL job')
    parser.add_argument('--job-name', type=str, default='longline-vessel-etl',
                        help='Name of the Glue job to trigger (default: longline-vessel-etl)')
    parser.add_argument('--region', type=str, default='us-east-1',
                        help='AWS region (default: us-east-1)')
    parser.add_argument('--wait', action='store_true',
                        help='Wait for the job to complete')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO', help='Set the logging level')
    
    args = parser.parse_args()
    
    # Set the log level based on the command-line argument
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        trigger_glue_job(args.job_name, args.wait, args.region)
    except Exception as e:
        logger.exception(f"Error triggering Glue job: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 