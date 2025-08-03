Current=$(pwd)
echo $Current
cd ./text2pydough/workbench/ARamirez/prompt_evaluation/
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../" && pwd)"
echo $BASE_DIR
# Set up all required paths
DB_PATH="${BASE_DIR}/mount-folder/datasets/"
METADATA_PATH="${BASE_DIR}/mount-folder/datasets/"

(cd "${BASE_DIR}/mount-folder/datasets/Defog/databases" && bash setup_defog.sh)

python prompt_evaluation_gradio.py \
    --description "Running defog questions with metadata 2.0: Metadata in user prompt side." \
    --name "Defog 124 metadata 2.0, 8-1 question changes" \
    --experiment_name "Ensemble" \
    --db-base-path "${DB_PATH}" \
    --metadata-base-path "${METADATA_PATH}" \
    --pydough_file "${BASE_DIR}/text2pydough/workbench/JSolano/prompt_evaluation/data/pydough_files/cheatsheet_8_1.md" \
    --prompt_file "${BASE_DIR}/text2pydough/workbench/JSolano/prompt_evaluation/data/prompts/prompt_8_1.md" \
    --questions "${BASE_DIR}/text2pydough/workbench/JSolano/prompt_evaluation/test_csv/complete_corrected_questions_8_1_gtj_with_id.csv" \
    --provider google \
    --model_id ensemble \
    --num_threads 10 \
    --keys 1 2 3 4 5 6 \
    --use-parallel \
    --ensemble-selection-method "size" \
    --tries 6 \
    --extra_args --temperature 0.0 --use_stream True
cd $Current
