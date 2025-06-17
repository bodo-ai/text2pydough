#!/bin/bash

# Exit on error
set -e

# Get the absolute path of the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Debug output
echo "Script directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT"
echo "Looking for .env file at: $PROJECT_ROOT/.env"

# Load environment variables from .env file
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Found .env file"
    echo "Contents of .env file:"
    cat "$PROJECT_ROOT/.env"
    echo "Loading environment variables..."
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
    echo "Environment variables loaded"
else
    echo "Error: .env file not found in $PROJECT_ROOT"
    echo "Expected path: $PROJECT_ROOT/.env"
    exit 1
fi

# Debug output for AWS credentials
echo "Checking AWS credentials..."
echo "AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:+set}"
echo "AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:+set}"

# Install R2R with core dependencies
echo "Installing R2R with core dependencies..."
pip install 'r2r[core]'

# Set up R2R configuration for AWS Bedrock
echo "Setting up R2R configuration for AWS Bedrock..."

# Create r2r.toml configuration file
cat > r2r.toml << EOL
[default]
embedding_model = "bedrock"
embedding_dim = 1536
embedding_batch_size = 100
embedding_provider = "bedrock"
embedding_model_name = "amazon.titan-embed-text-v1"

[bedrock]
region_name = "${AWS_DEFAULT_REGION:-us-east-1}"
model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
max_tokens = 4096
temperature = 0.0

[llm]
provider = "bedrock"
model = "anthropic.claude-3-sonnet-20240229-v1:0"

[database]
provider = "cloud"
user = "${R2R_CLOUD_USER:-default}"
password = "${R2R_CLOUD_PASSWORD:-default}"
host = "${R2R_CLOUD_HOST:-api.r2r.cloud}"
port = "${R2R_CLOUD_PORT:-443}"
dbname = "${R2R_CLOUD_DBNAME:-default}"
EOL

# Set required environment variables
export R2R_CONFIG_NAME="default"
export R2R_PROJECT_NAME="pydough"

# Verify AWS credentials are set
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Error: AWS credentials not found in .env file"
    echo "Please ensure your .env file in $PROJECT_ROOT contains AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
    echo "Current AWS_ACCESS_KEY_ID: $AWS_ACCESS_KEY_ID"
    echo "Current AWS_SECRET_ACCESS_KEY: $AWS_SECRET_ACCESS_KEY"
    exit 1
fi

# Start R2R server
echo "Starting R2R server..."
python -m r2r.serve 