python prompt_evaluation_gradio.py \
  --description "Running size selection with the all_runs file" \
  --name "Size Selection with all_runs file" \
  --experiment_name "EnsembleOnly" \
  --all-runs /home/j/text2pydough/workbench/ARamirez/prompt_evaluation/test_csv/all_model_runs_2025_08_02-02_23_06.csv \
  --ensemble-selection-method size \
  --ensemble-output-dir /home/j/text2pydough/workbench/ARamirez/prompt_evaluation/test_csv/eval_outputs \
  --db-base-path /home/j/text2pydough/workbench/JSolano/prompt_evaluation/test_data/ \
  --metadata-base-path /home/j/text2pydough/workbench/JSolano/prompt_evaluation/test_data/ \