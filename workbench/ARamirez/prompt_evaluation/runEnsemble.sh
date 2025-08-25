DB_PATH=/home/j/text2pydough/workbench/JSolano/prompt_evaluation/test_data/
METADATA_PATH=/home/j/text2pydough/workbench/JSolano/prompt_evaluation/test_data/

(cd test_data/databases/Defog && ./setup_defog.sh)

python prompt_evaluation.py \
    --description "Running models with the new columns" \
    --name "Ensemble Run Gemini 2.5 Pro & Claude Opus 4" \
    --experiment_name "Ensemble" \
    --db-base-path "${DB_PATH}" \
    --metadata-base-path "${METADATA_PATH}" \
    --pydough_file "data/8_1 files/cheatsheet_8_1.md" \
    --prompt_file "data/8_1 files/prompt_8_1.md" \
    --questions "data/8_1 files/complete_corrected_questions_8_1_gtj_with_id.csv" \
    --provider google \
    --model_id ensemble \
    --num_threads 1 \
    --keys 1 \
    --use-parallel \
    --ensemble-selection-method "size" \
    --tries 6 \
    --extra_args --temperature 0.0 --use_stream True