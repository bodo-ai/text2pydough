# Script for Processing Questions and Prompt with AI Model

This script processes a set of questions against a script and database, generating responses using a specified AI model. The AI model can be from either Azure or another provider, and responses are saved to a CSV file.


## Installation

1. Clone or download the repository.
2. Install the environment using conda

## Conda install

under workbench/ARamirez/prompt_evaluation
conda env create -f environment.yml
pip install pydough 

## For AWS

Install aws cli:
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

Once installed, configure it using "aws configure" and add your AWS Access Key and AWS Secret Key

To get Access Key ID ... 



## Setup
Before running the script, set the following environment variables

For azure models:
```bash
export AZURE_BASE_URL="your_azure_endpoint"
export GITHUB_TOKEN="your_azure_api_token"
```

For openai models: 
```bash
export OPENAI_API_KEY="your_openai_api_key" 
```

For aws models:
```bash
export AWS_ACCESS_KEY="your-access-key"
export AWS_SECRET_KEY="your-secret-key"
export AWS_REGION="region-name"
```

For deepseek models:
```bash
export DEEPSEEK_API_KEY="your-deepseek-api-key"
```

## Usage
Run the script with the following command:

```bash
python prompt_evaluation.py <script_file> <database_structure> <prompt_file> <questions_csv> <provider> <model_id>
```
**Arguments:**

- `<script_file>`: "Path to the script file."
- `<database_structure>`: "Path to the database file."
- `<prompt_file>`: "Path to the prompt file."
- `<questions_csv>`: "Path to the questions CSV file."
- `<provider>`: "Model provider (either 'azure' or another provider)."
- `<model_id>`: "Model ID to use."
