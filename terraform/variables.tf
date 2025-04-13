variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project, used in resource naming"
  type        = string
  default     = "fishing-anomaly-detection"
}

variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
  default     = "fishing-anomaly-detection-1744553260"
}

variable "glue_database_name" {
  description = "Name of the Glue database"
  type        = string
  default     = "fishing_vessel_data"
}

variable "tags" {
  description = "Tags to set on resources"
  type        = map(string)
  default = {
    Project     = "fishing-anomaly-detection"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
} 