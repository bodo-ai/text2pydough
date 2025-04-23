# Script for Processing Questions and Prompt with AI Model

This script processes a set of questions against a script and database, generating responses using gemini. 

## 📁 Project Structure

```
.
├── run_questions.py          # Entry point for executing the generation/evaluation
├── queries_context.json         # JSON with contextual metadata per question
├── test_data/
│   ├── eval.py                  # Evaluation functions
│   └── TPCH_graph.json          # metadata to use pydough dsl
├── results/                     # Output folder for generated CSV results
├── prompt.md/                   # Prompt file 
├── cheatsheet.md/               # File that describes the usage of pydough 
├── TPCH_graph.md/               # Description in plain english of the TPCH database
```
---

## 🛠️ Installation

1. Clone or download the repository.
2. Install the environment using conda

## Conda install

conda env create -f environment.yml 

## Setup
Before running the script, set the following environment variables

For google models:
```bash
export GOOGLE_PROJECT_ID="your-project-id"
export GOOGLE_REGION="your-region"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-file.json"
export GOOGLE_API_KEY= "api key"
```

Download the TPCH database by running the `setup_tpch.sh`

```bash
bash setup_tpch.sh
```

---

## 🧲 Usage

### Run the script

```bash
python run_questions.py \
  --pydough_file cheatsheet.md \
  --prompt_file prompt.md \
  --questions questions.csv \
```

The temperature, top_p, and seed settings are currently hardcoded