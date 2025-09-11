cd ./text2pydough/workbench/ARamirez/prompt_evaluation/
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../" && pwd)"
echo $BASE_DIR
# Set up all required paths
DB_PATH="${BASE_DIR}/mount-folder/datasets/"
METADATA_PATH="${BASE_DIR}/mount-folder/datasets/"

python evaluate_all_runs.py \
  --all-runs all_runs_csv/eval_all_model_runs_2025_09_09_GEMINI.csv \
  --db-base-path "${DB_PATH}" \
  --metadata-base-path "${METADATA_PATH}" \
  --output-dir /home/jupyter/text2pydough/workbench/ARamirez/prompt_evaluation/test_csv/eval_outputs "$@" \
  --ensemble-methods size,frequency,random,density,indiv_agent_grade,binary_comp_selection \
  --tie-breakers size,random,density \
  --mlflow_uri "http://mlflow-alb-1071096006.us-east-2.elb.amazonaws.com" \
  --mlflow_experiment EnsembleOnly \
  --mlflow_run_name "69% run Gemini testing" \
  --mlflow_token "" \
  --use-eval-result-only \
  --original-mlflow-run "http://localhost:5000/#/experiments/11/runs/385c0ecf27ec4a74a6c9300236820158"