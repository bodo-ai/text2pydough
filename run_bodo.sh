numranks=10
export BODO_NUM_WORKERS="$numranks"


for i in {1..1}
do
    echo "Running iteration $i..."
    python "prompt_evaluation_bodo.py" \
        --pydough_file "data/cheatsheet.md" \
        --database_structure "data/tpch_graph.md" \
        --prompt_file "data/prompt.md" \
        --questions "/bodofs/Users/hadia/LLM/questions_only.csv" \
        --provider google \
        --model_id gemini-2.0-flash-lite \
        --temperature 0.0 \
        --num_threads $numranks \
        --num_iterations 1 >> "bodo_${numranks}_ranks.txt"
done

        #--questions "115_questions_only.csv" \
        #--questions "/bodofs/Users/hadia/LLM/questions_only.csv" \
        #--questions "/bodofs/Users/hadia/LLM/questions_all_bodo_write.pq" \
# Models:
# gemini-2.0-flash-thinking-exp-01-21
# gemini-2.0-flash-001   
# gemini-2.5-pro-exp-03-25
# provider: aws-deepseek, model_id: us.deepseek.r1-v1:0
# gemini-2.5-pro-preview-03-25
