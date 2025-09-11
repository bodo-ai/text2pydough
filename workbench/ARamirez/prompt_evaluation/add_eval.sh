cd ./text2pydough/workbench/ARamirez/prompt_evaluation/
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../" && pwd)"
echo $BASE_DIR
# Set up all required paths
DB_PATH="${BASE_DIR}/mount-folder/datasets/"
METADATA_PATH="${BASE_DIR}/mount-folder/datasets/"

python eval_all_runs_to_csv.py \
  --all-runs all_runs_csv/BIRD_10.csv \
  --db-base-path "${DB_PATH}" \
  --metadata-base-path "${METADATA_PATH}" \
  --num-threads 16