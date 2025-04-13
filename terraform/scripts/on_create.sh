#!/bin/bash
set -e

# Install required packages in the Jupyter environment
sudo -u ec2-user -i <<'EOF'
# Create and activate conda environment
conda create -n fishing_anomaly python=3.8 -y
source activate fishing_anomaly

# Install packages
pip install boto3 pandas numpy matplotlib seaborn scikit-learn recordio sagemaker

# Create directories for scripts and notebooks
cd /home/ec2-user/SageMaker
mkdir -p fishing-anomaly
mkdir -p fishing-anomaly/scripts

echo "Setup Complete"
EOF 