#!/bin/bash
set -e

# Start the fishing_anomaly conda environment
sudo -u ec2-user -i <<'EOF'
source activate fishing_anomaly
echo "Activated fishing_anomaly environment"
EOF 