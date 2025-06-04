#!/bin/bash

# Exit on error
set -e

# Print commands as they are executed
set -x

# Set base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

# Ensure BASE_DIR is added to PYTHONPATH so Python can find the 'generator_team' package
export PYTHONPATH="${BASE_DIR}:${PYTHONPATH}"

# Set up paths that remain fixed
CHEATSHEET_PATH="${BASE_DIR}/generator_team/pydough_data/pydough_files/cheatsheet_partition_overhaul.md"
# QUESTIONS_CSV_PATH should point to the benchmark containing per-row dataset info
QUESTIONS_CSV_PATH="${BASE_DIR}/generator_team/eval_data/defog/combined_results_gemini_opus_QE.csv"
OUTPUT_DIR="${BASE_DIR}/generator_team/results"

# Default values for optional parameters
START_ROW=1
NUM_QUESTIONS=15
AGENT_TYPE="sql"
AGENT_PATH="${BASE_DIR}/generator_team/agents/SelfHealingReact.py"
DATASET_NAME=""
MODEL_NAME="gemini-2.5-flash-preview-05-20" # "gemini-2.5-pro-preview-05-06"
#Default model name "gemini-2.5-pro-preview-05-06" 
#
FILTER_QUERY_ERRORS=false  # Filter for "Query Error" in comparison results

# Create output directory if it doesn't exist
mkdir -p "${OUTPUT_DIR}"

# Run the sequential evaluation script
python "${BASE_DIR}/generator_team/sequential_eval.py" \
    --cheatsheet-path "${CHEATSHEET_PATH}" \
    --questions-csv-path "${QUESTIONS_CSV_PATH}" \
    --output-dir "${OUTPUT_DIR}" \
    --start-row "${START_ROW}" \
    --num-questions "${NUM_QUESTIONS}" \
    --agent-type "${AGENT_TYPE}" \
    --agent-path "${AGENT_PATH}" \
    --dataset-name "${DATASET_NAME}" \
    --model-name "${MODEL_NAME}" \
    --filter-query-errors "${FILTER_QUERY_ERRORS}" \
    "$@"

# Print completion message
echo "Sequential evaluation completed successfully!" 