from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from pathlib import Path
import dspy
import json
import os
import re
import textwrap
import pydough


load_dotenv()

EVALUATION_PROMPT = """You are an expert data analyst evaluating the quality of DataFrames returned for specific questions.


Question asked: {question}
DataFrame result: {dataframe}

Evaluate it on these criteria:
- Empty DataFrames or incorrect structure: Verify the DataFrame contains data and has the expected columns and rows  
Columns that don't answer the question: Ensure all included columns are relevant to the user's query  
- Unnecessary duplicate data: Identify and handle redundant rows or information that doesn't add value  
- Inappropriate data types for the query: Confirm data types (numeric, string, datetime) are suitable for the analysis  
Missing critical information to answer the question: Verify all essential data needed to address the query is present  
- Inadequate ordering of results: Check that results are sorted in a logical, meaningful way for the user  
Communication quality: Is the DataFrame structure clear, concise, and free of data inconsistencies? Assess whether the presentation is easy to understand, properly formatted, and contains accurate, consistent data throughout.
Important: Be thorough but not overly strict. Minor stylistic variations, synonyms, or differences in ordering should not incur large penalties as long as the essential information is present and correct.
Guidelines: 
 Use a score from 0 to 10
- Score 8-10: Excellent/optimal for the question
- Score 5-7: Good with minor improvements needed
- Score 3-4: Adequate but with significant room for improvement  
- Score 0-2: Severely lacking in that dimension
- Focus deductions on substantive omissions rather than minor variations.  
- Verify that the DataFrame addresses all items requested in the question.

You must respond with EXACTLY this JSON format (no additional text):
{{
    "score": [numerical value 0-10],
    "reasoning": "Brief explanation of the score"
}}
Example valid responses:
{{"score": 8, "reasoning": "DataFrame contains all required columns and data"}}
{{"score": 3, "reasoning": "Missing critical columns for the analysis"}}
REMEMBER: The score must ALWAYS be a number from 0 to 10, never True/False or other values.

"""


EVALUATION_BINARY_PROMPT = """You are an expert data analyst evaluating the quality of DataFrames returned for specific questions. You will have to choose between two dataframe options according to the following criteria 


Question asked: {question}
DataFrame 1: {dataframe_1}
DataFrame 2: {dataframe_2}

Evaluate it on these criteria:
- Empty DataFrames or incorrect structure: Verify the DataFrame contains data and has the expected columns and rows  
Columns that don't answer the question: Ensure all included columns are relevant to the user's query  
- Unnecessary duplicate data: Identify and handle redundant rows or information that doesn't add value  
- Inappropriate data types for the query: Confirm data types (numeric, string, datetime) are suitable for the analysis  
Missing critical information to answer the question: Verify all essential data needed to address the query is present  
- Inadequate ordering of results: Check that results are sorted in a logical, meaningful way for the user  
Communication quality: Is the DataFrame structure clear, concise, and free of data inconsistencies? Assess whether the presentation is easy to understand, properly formatted, and contains accurate, consistent data throughout.
Important: Be thorough but not overly strict. Minor stylistic variations, synonyms, or differences in ordering should not incur large penalties as long as the essential information is present and correct.
Guidelines: 
 Use a score from 0 to 10
- Score 8-10: Excellent/optimal for the question
- Score 5-7: Good with minor improvements needed
- Score 3-4: Adequate but with significant room for improvement  
- Score 0-2: Severely lacking in that dimension
- Focus deductions on substantive omissions rather than minor variations.  
- Verify that the DataFrame addresses all items requested in the question.

You must respond with EXACTLY this JSON format (no additional text):
{{
"best_index": "index of the best df"
}}

Remember handle the indez like python
"""

class DataFrame_Evaluator(dspy.Signature):
    """Evaluate the quality of a DataFrame result for a specific database query."""

    question: str = dspy.InputField(desc="The original question asked by the user")
    dataframe: str = dspy.InputField(desc="String representation of the DataFrame result to evaluate")
    evaluation_criteria: str = dspy.InputField(desc="Detailed criteria for evaluating DataFrame quality")
    evaluation: str = dspy.OutputField(desc="JSON evaluation with score (0-10) and reasoning")


lm = dspy.LM('gemini/gemini-2.5-pro', api_key = os.getenv("GOOGLE_API_KEY_1"), temperature=0)
qa = dspy.ChainOfThought(DataFrame_Evaluator)

class DataFrame_Binary_Evaluator(dspy.Signature):
    """Evaluate the quality of a DataFrame result for a specific database query."""

    question: str = dspy.InputField(desc="The original question asked by the user")
    dataframe_1: str = dspy.InputField(desc="String representation of the DataFrame result to evaluate")
    dataframe_2: str = dspy.InputField(desc="String representation of the DataFrame result to evaluate")
    evaluation_criteria: str = dspy.InputField(desc="Detailed criteria for evaluating DataFrame quality")
    evaluation: str = dspy.OutputField(desc="JSON evaluation with score (0-10) and reasoning")


bi = dspy.ChainOfThought(DataFrame_Binary_Evaluator)


def extract_json_evaluation(text):
    try:
        # Buscar JSON en la respuesta
        json_match = re.search(r'\{[^{}]*"score"[^{}]*\}', text)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {"score": 0, "reasoning": "Could not parse evaluation"}
    except json.JSONDecodeError:
        return {"score": 0, "reasoning": "Invalid JSON format"}

def evaluate_dataframes_csv():
    df = pd.read_csv("prueba.csv")    
    results = []
    for i, row in df.iterrows():
        question = row["question"]
        db_name = row["db_name"]        
        dataframe_str = (row.get("gen_df_json", ""))  
        with dspy.context(lm=lm):
            response = qa(
                question=question,
                dataframe=dataframe_str,
                evaluation_criteria=EVALUATION_PROMPT
            )
            print(f"Question: {question}")
            print(f"Evaluation: {response.evaluation}")
            print("-" * 50)
            results.append({
                'question': question,
                'dataframe': dataframe_str,
                'evaluation': response.evaluation
            })
        break
    return results


def evaluate_single_dataframe(question, dataframe_str):
    with dspy.context(lm=lm):
        response = qa(
            question=question,
            dataframe=dataframe_str,
            evaluation_criteria=EVALUATION_PROMPT
        )
        
        evaluation_json = extract_json_evaluation(response.evaluation)
        return evaluation_json.get("score", 0) 
    
def evaluate_binary_dataframes(question, dataframes_list):  
    df_1 = dataframes_list[0]
    df_2 = dataframes_list[1]  
    with dspy.context(lm=lm):
        response = bi(
            question=question,
            dataframe_1=df_1,
            dataframe_2=df_2,
            evaluation_criteria=EVALUATION_BINARY_PROMPT
        )
    evaluation_data = json.loads(response.evaluation)
    best_index = evaluation_data["best_index"]    
    return best_index

def evaluate_dataframes(question, dataframes_list):
    best_score = -1
    best_index = 0 
    for i, dataframe_str in enumerate(dataframes_list):
        score = evaluate_single_dataframe(question, dataframe_str)
        
        if score > best_score:
            best_score = score
            best_index = i
    return best_index

if __name__ == "__main__":
    
    sample_question = "What are the sales by region?"
    sample_dataframes = [
        "DataFrame 1: {'region': ['North', 'South', 'East'], 'sales': [100, 200, 150], 'product': ['A', 'B', 'C']}",
        "DataFrame 2: {'region': ['North', 'South'], 'sales': [100, 200]}",
        "DataFrame 3: {'total_sales': [450]}"
    ]

    
    best_index = evaluate_binary_dataframes(sample_question, sample_dataframes)
    print(f"Índice del mejor DataFrame: {best_index}")
