#!/bin/bash

THREAD_COUNTS=(36)
ITERATION_COUNTS=(10 20) #100 1000)
LOG_DIR="logs"
SUMMARY_CSV="summary.csv"

mkdir -p "$LOG_DIR"
echo "mode,threads,iterations,time_sec,output_file" > "$SUMMARY_CSV"

for threads in "${THREAD_COUNTS[@]}"; do
  for iterations in "${ITERATION_COUNTS[@]}"; do
    echo "Running with $threads threads and $iterations iterations"

    # No Bodo
    log_no_bodo="${LOG_DIR}/no_bodo_t${threads}_i${iterations}.log"
    ./run_no_bodo.sh "$threads" "$iterations" > "$log_no_bodo" 2>&1
    result_line=$(grep "\[RESULT\]" "$log_no_bodo")
    if [ -n "$result_line" ]; then
      mode=$(echo "$result_line" | sed -n 's/.*mode=\([^ ]*\).*/\1/p')
      time=$(echo "$result_line" | sed -n 's/.*time=\([^ ]*\).*/\1/p')
      out_file=$(echo "$result_line" | sed -n 's/.*output_file=\(.*\)/\1/p')
      echo "$mode,$threads,$iterations,$time,$out_file" >> "$SUMMARY_CSV"
    fi

    # Bodo
    log_bodo="${LOG_DIR}/bodo_t${threads}_i${iterations}.log"
    ./run_bodo.sh "$threads" "$iterations" > "$log_bodo" 2>&1
    result_line=$(grep "\[RESULT\]" "$log_bodo")
    if [ -n "$result_line" ]; then
      mode=$(echo "$result_line" | sed -n 's/.*mode=\([^ ]*\).*/\1/p')
      time=$(echo "$result_line" | sed -n 's/.*time=\([^ ]*\).*/\1/p')
      out_file=$(echo "$result_line" | sed -n 's/.*output_file=\(.*\)/\1/p')
      echo "$mode,$threads,$iterations,$time,$out_file" >> "$SUMMARY_CSV"
    fi

    echo "-----------------------------------------"
  done
done

echo "Summary written to $SUMMARY_CSV"

