#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Run evaluate_all_runs.py on the large all_model_runs CSV.
# Adjust --num-threads if you want to control parallelism (defaults to CPU count).
# -----------------------------------------------------------------------------

python /home/j/text2pydough/workbench/ARamirez/prompt_evaluation/evaluate_all_runs.py \
  --all-runs /home/j/text2pydough/workbench/ARamirez/prompt_evaluation/test_csv/all_model_runs_2025_08_02-23_58_06.csv \
  --db-base-path /home/j/text2pydough/workbench/JSolano/prompt_evaluation/test_data/ \
  --metadata-base-path /home/j/text2pydough/workbench/JSolano/prompt_evaluation/test_data/ \
  --output-dir /home/j/text2pydough/workbench/ARamirez/prompt_evaluation/test_csv/eval_outputs "$@" \
  --num_threads 10