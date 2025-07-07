#!/bin/bash
# Set base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
echo $BASE_DIR
# Set up all required paths
DB_PATH="${BASE_DIR}/mount-folder/datasets"
METADATA_PATH="${BASE_DIR}/mount-folder/datasets"
CHEATSHEET_PATH="${BASE_DIR}/text2pydough/workbench/lcar_lab/labeling_agent/pydough_data/pydough_files/cheatsheet_partition_overhaul.md"
QUESTIONS_CSV_PATH="${BASE_DIR}/mount-folder/labeling_data/gemini_2.0_flash/20250623_151356/results.csv"
OUTPUT_DIR="${BASE_DIR}/mount-folder/labeling_data/gemini_2.5_flash"
# Default values for optional parameters
START_ROW=0
NUM_QUESTIONS=1000
CONCURRENT_QUESTIONS=5
MAX_FEEDBACK_LOOPS=5
# Create output directory if it doesn't exist
#mkdir -p "${OUTPUT_DIR}"
# Run the async labeling script with all paths
python "${BASE_DIR}/text2pydough/workbench/lcar_lab/labeling_agent/async_orchestrator_m2.py" \
    --output-dir "${OUTPUT_DIR}" \
    --db-base-path "${DB_PATH}" \
    --metadata-base-path "${METADATA_PATH}" \
    --cheatsheet-path "${CHEATSHEET_PATH}" \
    --questions-csv-path "${QUESTIONS_CSV_PATH}" \
    --start-row "${START_ROW}" \
    --num-questions "${NUM_QUESTIONS}" \
    --concurrent-questions "${CONCURRENT_QUESTIONS}" \
    --max-feedback-loops "${MAX_FEEDBACK_LOOPS}" \
    "$@"