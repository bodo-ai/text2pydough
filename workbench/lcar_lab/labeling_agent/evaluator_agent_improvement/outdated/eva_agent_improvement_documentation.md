# Evaluator Agent Improvement Documentation

The `200_testing_dataset.csv` contains 200 examples of False dataframe match after running spider dataset using labeling agent. The idea now is to improve the evaluator agent to get more True results. 

All the results are going to be tested with gemini 2.0 flash and claud 3.7. Every run will be saved into the model->iteration# directory. 

## 1° iteration

No changes, just to test if the model improve the current testing dataset and it starts from there. 

VALUES
- FEEDBACK_LOOPS: 7
- RUNS BY MODEL: 1

RESULTS
- Gemini 2.0-flash: 16% of variation
- Gemini 2.5-flash: 
- Claud 3.7: The original 200_testing_dataset file was generated with gemini 2.0 flash. Then the first result of claud 3.7 give a comparison between the base gemini 2.0 flash result and the claud 3.7 result. Claud is better with a 42% of variation. 
  
## 2° iteration

Add the cheatsheet to the evaluator agent prompt. 

VALUES
- FEEDBACK_LOOPS: 7
- RUNS BY MODEL: 1
- CHEATSHEET: cheatsheet_partition_overhaul.md