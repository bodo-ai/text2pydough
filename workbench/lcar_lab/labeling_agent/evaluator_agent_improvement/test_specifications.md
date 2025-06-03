# Labeling Agent Improvement

## Models
- Test with gemini 2.5 flash and claud 4.0 soonet models.
  
## Selected dataset 
- Create a dataset with 200 questions that meet: 
  - Questions outside training, testing, golden and validation datasets
  - High level of difficulty
  - Dataframe_match equal to false

## Tests
- Use the new eval function. 
- Run and merge 3 (or more if this is continue working) results of claude 4.0 soonet and gemini 2.5 flash (using 7 feedback loops)
- Add the metadata to the evaluator agent. 
- Add the cheatsheet to the evaluator agent. 

## Goal
- Convert the 80% of False data to True data for training purposes. 