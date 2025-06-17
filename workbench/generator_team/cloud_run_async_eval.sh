#!/bin/bash

# Set base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Add generator_team to PYTHONPATH
export PYTHONPATH="${BASE_DIR}:${PYTHONPATH}"

# Set up all required paths
DB_PATH="${BASE_DIR}/mount-folder/datasets/TPCH/TPC-H.db"
METADATA_PATH="${BASE_DIR}/mount-folder/datasets/TPCH/tpch_demo_graph.json"
CHEATSHEET_PATH="${BASE_DIR}/generator_team/pydough_data/pydough_files/cheatsheet_partition_overhaul.md"
QUESTIONS_CSV_PATH="${BASE_DIR}/mount-folder/datasets/TPCH/benchmark.csv"
OUTPUT_DIR="${BASE_DIR}/generator_team/results"

# Default values for optional parameters
START_ROW=0
NUM_QUESTIONS=71
CONCURRENT_QUESTIONS=3
MAX_FEEDBACK_LOOPS=1
TEMPERATURE=0.7
TOP_P=0.95
export EXPERIMENT_NAME="Finetuned Model gemini-2.0-flash-finetune-v0.11.2 ReAct Langgraph"

# decide whether to load in context the cheatsheet
USE_CHEATSHEET=true
#true

# set the vertexai model name for the PyDough generator
MODEL_NAME="gemini-2.5-pro-preview-03-25"

# Create output directory if it doesn't exist
#mkdir -p "${OUTPUT_DIR}"

# Run the async labeling script with all paths
python "${BASE_DIR}/generator_team/async_evaluation_run.py" \
    --output-dir "${OUTPUT_DIR}" \
    --db-path "${DB_PATH}" \
    --metadata-path "${METADATA_PATH}" \
    --cheatsheet-path "${CHEATSHEET_PATH}" \
    --questions-csv-path "${QUESTIONS_CSV_PATH}" \
    --start-row "${START_ROW}" \
    --num-questions "${NUM_QUESTIONS}" \
    --concurrent-questions "${CONCURRENT_QUESTIONS}" \
    --max-feedback-loops "${MAX_FEEDBACK_LOOPS}" \
    --use-cheatsheet "${USE_CHEATSHEET}" \
    --model-name "${MODEL_NAME}" \
    --experiment-name "${EXPERIMENT_NAME}" \
    "$@" 
