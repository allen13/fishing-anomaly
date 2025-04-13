output "s3_bucket_name" {
  description = "Name of the S3 bucket storing fishing data"
  value       = data.aws_s3_bucket.fishing_data_bucket.bucket
}

output "raw_data_location" {
  description = "S3 location of raw fishing data"
  value       = "s3://${data.aws_s3_bucket.fishing_data_bucket.bucket}/raw/"
}

output "processed_data_location" {
  description = "S3 location of processed fishing data"
  value       = "s3://${data.aws_s3_bucket.fishing_data_bucket.bucket}/processed/"
}

output "aggregated_data_location" {
  description = "S3 location of aggregated vessel data"
  value       = "s3://${data.aws_s3_bucket.fishing_data_bucket.bucket}/aggregated/"
} 