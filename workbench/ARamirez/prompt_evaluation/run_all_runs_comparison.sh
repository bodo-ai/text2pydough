cd ./text2pydough/workbench/ARamirez/prompt_evaluation/
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../" && pwd)"
echo $BASE_DIR
# Set up all required paths
DB_PATH="${BASE_DIR}/mount-folder/datasets/"
METADATA_PATH="${BASE_DIR}/mount-folder/datasets/"

python evaluate_all_runs.py \
  --all-runs all_runs_csv/BIRD_finetuned_all_model_2025_08_26.csv \
  --db-base-path "${DB_PATH}" \
  --metadata-base-path "${METADATA_PATH}"
  --output-dir /home/jupyter/text2pydough/workbench/ARamirez/prompt_evaluation/test_csv/eval_outputs "$@" \
  --num_threads 16