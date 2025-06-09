#!/bin/bash

# Set base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Add generator_team to PYTHONPATH
export PYTHONPATH="${BASE_DIR}:${PYTHONPATH}"

# Set up all required paths
DB_PATH="${BASE_DIR}/TPCH/test_data/tpch.db"
METADATA_PATH="${BASE_DIR}/TPCH/test_data/tpch_demo_graph.json"
CHEATSHEET_PATH="${BASE_DIR}/generator_team/pydough_data/pydough_files/cheatsheet_partition_overhaul.md"
QUESTIONS_CSV_PATH="${BASE_DIR}/TPCH/test_data/benchmark.csv"
OUTPUT_DIR="${BASE_DIR}/generator_team/results"

# Default values for optional parameters
START_ROW=1
NUM_QUESTIONS=1
CONCURRENT_QUESTIONS=1
MAX_FEEDBACK_LOOPS=1
EXPERIMENT_NAME="default_experiment"
TEMPERATURE=0.7
TOP_P=0.95

# decide whether to load in context the cheatsheet
USE_CHEATSHEET=true

# set the vertexai model name for the PyDough generator
export MODEL_NAME="gemini-2.0-flash"
#"gemini-2.5-pro-preview-03-25"
#"projects/316936339319/locations/us-central1/endpoints/4491730399348654080"

#"gemini-2.0-flash"

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
    --temperature "${TEMPERATURE}" \
    --top-p "${TOP_P}" \
    "$@" 