# IAM role for SageMaker
resource "aws_iam_role" "sagemaker_role" {
  name = "sagemaker-fishing-anomaly-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      }
    ]
  })
}

# Attach AWS managed policy for SageMaker
resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

# Custom policy for S3 access
resource "aws_iam_role_policy" "sagemaker_s3_access" {
  name   = "sagemaker-s3-access"
  role   = aws_iam_role.sagemaker_role.id
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
        Effect   = "Allow"
        Resource = [
          "arn:aws:s3:::${var.bucket_name}",
          "arn:aws:s3:::${var.bucket_name}/*"
        ]
      }
    ]
  })
}

# SageMaker notebook instance for model development
resource "aws_sagemaker_notebook_instance" "fishing_notebook" {
  name                    = "fishing-anomaly-notebook"
  role_arn                = aws_iam_role.sagemaker_role.arn
  instance_type           = "ml.t2.medium"
  volume_size             = 5
  default_code_repository = null

  tags = merge(var.tags, {
    Name = "fishing-anomaly-notebook"
  })
}

# SageMaker notebook lifecycle configuration
resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "fishing_notebook_config" {
  name = "fishing-notebook-config"

  on_create = base64encode(file("${path.module}/scripts/on_create.sh"))
  on_start = base64encode(file("${path.module}/scripts/on_start.sh"))

  # Reference to ensure that any files to be included actually exist
  depends_on = []
}

# Upload the training script to S3
resource "aws_s3_object" "sagemaker_train_script" {
  bucket = var.bucket_name
  key    = "scripts/sagemaker_train.py"
  source = "${path.module}/scripts/sagemaker_train.py"
  etag   = filemd5("${path.module}/scripts/sagemaker_train.py")
}

# Attach the lifecycle configuration to the notebook instance
resource "aws_sagemaker_notebook_instance_lifecycle_configuration_association" "fishing_notebook_association" {
  notebook_instance_name              = aws_sagemaker_notebook_instance.fishing_notebook.name
  lifecycle_configuration_name        = aws_sagemaker_notebook_instance_lifecycle_configuration.fishing_notebook_config.name
} 