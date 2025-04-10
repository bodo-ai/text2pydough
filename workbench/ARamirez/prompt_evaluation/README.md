# Script for Processing Questions and Prompt with AI Model

This script processes a set of questions against a script and database, generating responses using a specified AI model. The AI model can be from either Azure or another provider, and responses are saved to a CSV file.

## 📁 Project Structure

```
.
├── prompt_evaluation.py          # Entry point for executing the generation/evaluation
├── queries_context.json         # JSON with contextual metadata per question
├── test_data/
│   ├── eval.py                  # Evaluation functions
│   └── tpch.db                  # SQLite DB for validation 
├── utils.py                     # Git helpers
├── claude.py                    # Claude client wrapper
├── results/                     # Output folder for generated CSV results
├── data/                        # Folder containing all resources
│   ├── pydough_files/           # Folder containing all available Pydough files in plain English
│   ├── queries/                 # Folder with all available question files and benchmark
│   ├── database/                # Folder with all database structure files
│   └── prompts/                 # Folder with all prompt files

```
---

## 🛠️ Installation

1. Clone or download the repository.
2. Install the environment using conda

## Conda install

under workbench/lcar_lab/mlflow_experiments
conda env create -f environment.yml 

## For AWS

Install aws cli:
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

Once installed, configure it using "aws configure" and add your AWS Access Key and AWS Secret Key

## For Google
Create a service account in Google Cloud Console, generate a JSON key and then move this file to a location on your file system like your home directory. 

## Setup
Before running the script, set the following environment variables

For google models:
```bash
export GOOGLE_PROJECT_ID="your-project-id"
export GOOGLE_REGION="your-region"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-file.json"
```

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
---

## 🧲 Usage

### Run the script

```bash
python prompt_evaluation.py \
  --description "testing an experiment" \
  --name "Gemini"
  --pydough_file ./data/pydough_functions/cheatsheet_v6.md \
  --database_structure ./data/database/tpch_graph.md \
  --prompt_file ./data/prompts/prompt.md \
  --questions_csv ./data/queries/benchmark.csv \
  --provider gemini \
  --model_id gemini-2.0-flash-001 \
  --temperature 0.7 \
  --num_threads 4
```

### Arguments

| Argument               | Description |
|------------------------|-------------|
| `--description`        | Description of the experiment. |
| `--name`               | Name of the the experiment. |
| `--pydough_file`       | Path to pydough that include description and functions in plain english. |
| `--database_structure` | File containing DB schema or structure in plain english. |
| `--prompt_file`        | File containing the prompt template. |
| `--questions`          | CSV with natural language questions. |
| `--provider`           | AI provider (`azure`, `aws-thinking`, `aws-deepseek`, or others). |
| `--model_id`           | LLM model ID (e.g., `gpt-4`, `gemini-2.0-flash-001`). |
| `--temperature`        | Sampling temperature for response creativity. |
| `--num_threads`        | Number of threads to use during execution. |

---

## 🧆 Git Integration

If the script detects untracked or modified files, it will automatically commit changes to capture the current Git hash for reproducibility.

---

## 📅 Example Prompt Format

```txt
### Instructions:
You are a Pydough translator. Convert the following question into valid Pydough code using the given schema and similar examples.

### Script:
{script_content}

### Database:
{database_content}

### Contextual Guidance:
{recomendation}
```

