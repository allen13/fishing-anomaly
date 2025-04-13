# AWS Glue job for vessel movement data ETL and aggregation
resource "aws_s3_object" "longline_etl_script" {
  bucket = var.bucket_name
  key    = "scripts/longline_etl.py"
  source = "../glue/longline_etl.py"
  etag   = filemd5("../glue/longline_etl.py")
}

# Longline data ETL and aggregation job
resource "aws_glue_job" "longline_etl" {
  name         = "longline-vessel-etl"
  role_arn     = aws_iam_role.glue_role.arn
  glue_version = "3.0"

  command {
    name            = "glueetl"
    script_location = "s3://${var.bucket_name}/scripts/longline_etl.py"
    python_version  = "3"
  }

  default_arguments = {
    "--enable-metrics"                   = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--job-language"                     = "python"
    "--input_path"                       = "s3://${var.bucket_name}/raw/"
    "--output_path"                      = "s3://${var.bucket_name}/aggregated/"
    "--TempDir"                          = "s3://${var.bucket_name}/temp/"
  }

  execution_property {
    max_concurrent_runs = 1
  }

  timeout = 60 # 1 hour timeout

  # Worker configuration
  worker_type       = "G.1X"
  number_of_workers = 2

  # Dependencies
  depends_on = [
    aws_s3_object.longline_etl_script
  ]
}