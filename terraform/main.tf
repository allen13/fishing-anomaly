provider "aws" {
  region = "us-east-1"
}

# Store Terraform state in S3
terraform {
  backend "s3" {
    bucket = "fishing-anomaly-detection-1744553260"
    key    = "terraform/state/terraform.tfstate"
    region = "us-east-1"
  }
}

# Reference the existing S3 bucket as a data source since it already exists
data "aws_s3_bucket" "fishing_data_bucket" {
  bucket = "fishing-anomaly-detection-1744553260"
}

# Create S3 directory structure
resource "aws_s3_object" "raw_directory" {
  bucket       = data.aws_s3_bucket.fishing_data_bucket.bucket
  key          = "raw/"
  content_type = "application/x-directory"
}

resource "aws_s3_object" "processed_directory" {
  bucket       = data.aws_s3_bucket.fishing_data_bucket.bucket
  key          = "processed/"
  content_type = "application/x-directory"
}

resource "aws_s3_object" "models_directory" {
  bucket       = data.aws_s3_bucket.fishing_data_bucket.bucket
  key          = "models/"
  content_type = "application/x-directory"
}

resource "aws_s3_object" "scripts_directory" {
  bucket       = data.aws_s3_bucket.fishing_data_bucket.bucket
  key          = "scripts/"
  content_type = "application/x-directory"
}

resource "aws_s3_object" "notebooks_directory" {
  bucket       = data.aws_s3_bucket.fishing_data_bucket.bucket
  key          = "notebooks/"
  content_type = "application/x-directory"
}

resource "aws_s3_object" "anomalies_directory" {
  bucket       = data.aws_s3_bucket.fishing_data_bucket.bucket
  key          = "anomalies/"
  content_type = "application/x-directory"
}

resource "aws_s3_object" "aggregated_directory" {
  bucket       = data.aws_s3_bucket.fishing_data_bucket.bucket
  key          = "aggregated/"
  content_type = "application/x-directory"
}

resource "aws_s3_object" "temp_directory" {
  bucket       = data.aws_s3_bucket.fishing_data_bucket.bucket
  key          = "temp/"
  content_type = "application/x-directory"
}

# IAM role for Glue
resource "aws_iam_role" "glue_role" {
  name = "glue-fishing-anomaly-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })
}

# Attach AWS managed policy for Glue service
resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# Custom policy for S3 access
resource "aws_iam_role_policy" "glue_s3_access" {
  name = "glue-s3-access"
  role = aws_iam_role.glue_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Effect = "Allow"
        Resource = [
          "arn:aws:s3:::${data.aws_s3_bucket.fishing_data_bucket.bucket}",
          "arn:aws:s3:::${data.aws_s3_bucket.fishing_data_bucket.bucket}/*"
        ]
      }
    ]
  })
} 