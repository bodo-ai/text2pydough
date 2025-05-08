export GOOGLE_PROJECT_ID="solid-drive-448717-p8"
export GOOGLE_REGION="us-central1"
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/solid-drive-448717-p8-757817f0ec29.json"
numranks=$1
numitr=$2

# input validation
if [[ -z "$numranks" || -z "$numitr" ]]; then
  echo "Usage: $0 <num_ranks> <num_iterations>"
  exit 1
fi
export BODO_NUM_WORKERS="$numranks"

python "prompt_evaluation_bodo.py" \
        --pydough_file "data/cheatsheet.md" \
        --database_structure "data/tpch_graph.md" \
	--questions "./question.txt" \
        --prompt_file "data/prompt.md" \
        --provider google \
        --model_id gemini-2.0-flash-lite \
        --temperature 0.0 \
        --num_threads "$numranks" \
        --num_iterations "$numitr"

        #--questions "/bodofs/Users/hadia/LLM/questions_only.csv" \
        #--questions "115_questions_only.csv" \
        #--questions "/bodofs/Users/hadia/LLM/questions_only.csv" \
        #--questions "/bodofs/Users/hadia/LLM/questions_all_bodo_write.pq" \
# Models:
# gemini-2.0-flash-thinking-exp-01-21
# gemini-2.0-flash-001   
# gemini-2.5-pro-exp-03-25
# provider: aws-deepseek, model_id: us.deepseek.r1-v1:0
# gemini-2.5-pro-preview-03-25
