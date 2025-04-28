#!/bin/bash

# Set base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
echo $BASE_DIR
# Set up all required paths
DB_PATH="${BASE_DIR}/mount-folder/datasets"
METADATA_PATH="${BASE_DIR}/mount-folder/datasets"
CHEATSHEET_PATH="${BASE_DIR}/labeling_agent/pydough_data/pydough_files/cheatsheet_partition_overhaul.md"
QUESTIONS_CSV_PATH="${BASE_DIR}/text2pydough/workbench/lcar_lab/labeling_agent/golden_dataset.csv"
OUTPUT_DIR="${BASE_DIR}/text2pydough/workbench/lcar_lab/labeling_agent/results"

# Default values for optional parameters
START_ROW=0
NUM_QUESTIONS=10
CONCURRENT_QUESTIONS=1

# Create output directory if it doesn't exist
#mkdir -p "${OUTPUT_DIR}"

# Run the async labeling script with all paths
python "${BASE_DIR}/text2pydough/workbench/lcar_lab/labeling_agent/async_orchestrator.py" \
    --output-dir "${OUTPUT_DIR}" \
    --db-base-path "${DB_PATH}" \
    --metadata-base-path "${METADATA_PATH}" \
    --cheatsheet-path "${CHEATSHEET_PATH}" \
    --questions-csv-path "${QUESTIONS_CSV_PATH}" \
    --start-row "${START_ROW}" \
    --num-questions "${NUM_QUESTIONS}" \
    --concurrent-questions "${CONCURRENT_QUESTIONS}" \
    "$@" 