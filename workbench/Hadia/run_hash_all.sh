#!/bin/bash

THREAD_COUNTS=(36 100)
ITERATION_COUNTS=(60 80 100)
LOG_DIR="logs"
SUMMARY_CSV="summary.csv"

mkdir -p "$LOG_DIR"
echo "mode,threads,iterations,time_sec,output_file" > "$SUMMARY_CSV"

for threads in "${THREAD_COUNTS[@]}"; do
  for iterations in "${ITERATION_COUNTS[@]}"; do
    echo "Running with $threads threads and $iterations iterations"

    # Bodo
    log_hash_bodo="${LOG_DIR}/no_bodo_t${threads}_i${iterations}.log"
    ./run_hash_bodo.sh "$threads" "$iterations" > "$log_hash_bodo" 2>&1
    result_line=$(grep "\[RESULT\]" "$log_hash_bodo")
    time_line=$(grep "Bodo ensemble time" "$log_hash_bodo")
    echo $time_line
    if [ -n "$result_line" ]; then
      mode=$(echo "$result_line" | sed -n 's/.*mode=\([^ ]*\).*/\1/p')
      time=$(echo "$time_line" | sed -n 's/.*time: \([^ ]*\).*/\1/p')
      out_file=$(echo "$result_line" | sed -n 's/.*output_file=\(.*\)/\1/p')
      echo "$mode,$threads,$iterations,$time,$out_file" >> "$SUMMARY_CSV"
    fi

    # Multiprocessing
    log_hash_mp="${LOG_DIR}/bodo_t${threads}_i${iterations}.log"
    ./run_hash_mp.sh "$threads" "$iterations" > "$log_hash_mp" 2>&1
    result_line=$(grep "\[RESULT\]" "$log_hash_mp")
    time_line=$(grep "Multiprocessing ensemble time" "$log_hash_mp")
    if [ -n "$result_line" ]; then
      mode=$(echo "$result_line" | sed -n 's/.*mode=\([^ ]*\).*/\1/p')
      echo "MODE: $mode"
      time=$(echo "$time_line" | sed -n 's/.*time: \([^ ]*\).*/\1/p')
      echo "Time: $time"
      out_file=$(echo "$result_line" | sed -n 's/.*output_file=\(.*\)/\1/p')
      echo "$mode,$threads,$iterations,$time,$out_file" >> "$SUMMARY_CSV"
    fi

    echo "-----------------------------------------"
  done
done

echo "Summary written to $SUMMARY_CSV"

