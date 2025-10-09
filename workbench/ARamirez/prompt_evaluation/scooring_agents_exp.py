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
import random

random.seed(12345)


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


EVALUATION_BINARY_PROMPT = """You are an expert data analyst comparing two candidate DataFrames for the same question. Evaluate both options and base your decision on concrete evidence from the data.

Question: {question}
Option A (index 0): {dataframe_1}
Option B (index 1): {dataframe_2}

Evaluate each option separately using this checklist:
- Non-empty with a valid shape (rows x columns)
- Columns directly answer the question; avoid extra/unasked columns
- No redundant/duplicate rows or columns
- Data types fit the analysis (e.g., numeric for math, date for time)
- Contains all information needed to answer the question
- Sorted/ordered as the question requests, if applicable
- Clear and consistent structure

Decision rule:
- Pick the option that better satisfies the checklist.
- If both are essentially equal, choose the one that more plausibly answers the question.
- Do not accept any extra columns aside from the explicitly indicated in the question.
- Prefer the option that has the columns closer to what the question asks, no lacking or extra information.

Additionally, provide a confidence score in the closed interval [0, 1] that reflects how strongly the evidence supports your choice (0 = no confidence, 1 = absolute confidence). The confidence should be based on how well the selected option satisfies the criteria relative to the other.

Output:
Return EXACTLY this JSON and nothing else:
{
    "best_index": 0,
    "confidence": 0.0
}
Where 0 means Option A and 1 means Option B (indices refer to the presented order above).
"""

EVALUATION_BINARY_PROMPT_ARA = """**You are an expert data analyst evaluating the quality of DataFrames returned for specific questions. You will have to choose between two dataframe options:**. 
Evaluate both options and base your decision on concrete evidence from the data and structure.
Question: {question}
Option A (index 0): {dataframe_1}
Option B (index 1): {dataframe_2}

Evaluate each option separately using this checklist:

1. **Non-empty and correct structure**: The DataFrame should not be empty and must include the appropriate columns and rows expected to answer the question.
2. **Relevance of columns**: All included columns must directly contribute to answering the question. Irrelevant or off-topic columns should be penalized.
3. **No unnecessary duplication**: Redundant rows or repeated information that do not provide additional value should be avoided.
4. **Appropriate data types**: Ensure that column data types (e.g., numeric, string, datetime) are suitable for the question being answered.
5. **Completeness of critical information**: All essential data needed to fully and accurately answer the question must be present.
6. **Logical ordering**: The results should be ordered in a meaningful way that makes the output easier to interpret, if ordering is relevant to the question.
7. **Communication and clarity**: The DataFrame should be well-structured, easy to understand, and free from inconsistencies, formatting issues, or ambiguous data presentation.
8. **SQL query quality**: When available, consider the quality, efficiency, and correctness of the corresponding SQL query that generated the DataFrame. A well-written SQL query that aligns with the DataFrame structure adds credibility to the candidate.

> ⚠️ **Be objective but not overly strict.** Minor stylistic differences, variations in column naming (e.g., synonyms), or row ordering should not result in a lower score if the core information is correct and complete.

Decision rule:
- Pick the option that better satisfies the checklist.
- If both are essentially equal, choose the one that more plausibly answers the question.

Additionally, provide a confidence score in the closed interval [0, 1] that reflects how strongly the evidence supports your choice (0 = no confidence, 1 = absolute confidence). The confidence should be based on how well the selected option satisfies the criteria relative to the other.

Output:
Return EXACTLY this JSON and nothing else:
{
    "best_index": 0,
    "confidence": 0.0
}
Where 0 means Option A and 1 means Option B (indices refer to the presented order above).
"""

EVALUATION_BINARY_WITH_CODE_PROMPT = """**You are an expert data analyst evaluating the quality of two candidate DataFrames for the same question. In addition to the DataFrames, you are given the associated PyDough code for each option when available. Choose the better option.**

Question: {question}
Option A (index 0) - DataFrame: {dataframe_1}
Option A - PyDough (if any):
{code_1}

Option B (index 1) - DataFrame: {dataframe_2}
Option B - PyDough (if any):
{code_2}

Evaluate each option separately using this checklist:

1. Non-empty and correct structure: The DataFrame should not be empty and must include appropriate columns and rows for the question.
2. Relevance of columns: All included columns must directly contribute to answering the question; penalize off-topic columns.
3. No unnecessary duplication: Avoid redundant rows or repeated information that do not add value.
4. Appropriate data types: Ensure column data types fit the analysis (numeric/date/text as needed).
5. Completeness of critical information: All essential data required to answer the question must be present.
6. Logical ordering: If ordering/sorting is relevant, it should be appropriate and helpful for interpretation.
7. Communication and clarity: Well-structured, easy to understand, consistent formatting.
8. PyDough code quality and alignment: When PyDough code is provided, prefer options whose code is more likely to correctly produce the shown DataFrame and answer the question (clear, plausible steps; no obvious logic errors or mismatches with the DataFrame).

Decision rule:
- Pick the option that better satisfies the checklist.
- If both are essentially equal, choose the one that more plausibly answers the question.

Additionally, provide a confidence score in the closed interval [0, 1] that reflects how strongly the evidence supports your choice (0 = no confidence, 1 = absolute confidence). Base this on how well the selected option satisfies the criteria relative to the other.

Output:
Return EXACTLY this JSON and nothing else:
{
    "best_index": 0,
    "confidence": 0.0
}
Where 0 means Option A and 1 means Option B (indices refer to the presented order above).
"""

class DataFrame_Evaluator(dspy.Signature):
    """Evaluate the quality of a DataFrame result for a specific database query."""

    question: str = dspy.InputField(desc="The original question asked by the user")
    dataframe: str = dspy.InputField(desc="String representation of the DataFrame result to evaluate")
    evaluation_criteria: str = dspy.InputField(desc="Detailed criteria for evaluating DataFrame quality")
    evaluation: str = dspy.OutputField(desc="JSON evaluation with score (0-10) and reasoning")


lm = dspy.LM('vertex_ai/gemini/projects/316936339319/locations/us-central1/endpoints/1012811837390979072', api_key = os.getenv("GOOGLE_API_KEY_1"), temperature=0, max_tokens = None)
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

def _parse_binary_evaluation(text):
    try:
        data = json.loads(text)
        best_index = data.get("best_index", 0)
        confidence = data.get("confidence", 0.0)
        try:
            best_index = int(best_index)
        except Exception:
            best_index = 0
        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0.0
        # Clamp confidence to [0,1]
        if confidence < 0:
            confidence = 0.0
        if confidence > 1:
            confidence = 1.0
        return best_index, confidence
    except Exception:
        return 0, 0.0

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

def evaluate_dataframe_with_description(question, dataframe_str, code_description):
    extended_criteria = f"""{EVALUATION_PROMPT}

Additional context to consider:
- Review the following description of the created code's functionality.
- Judge whether, if implemented as described, it would logically resolve the user's question and produce a correct DataFrame.
- If the description convincingly addresses the requirements and aligns with the DataFrame's structure/content, this should positively influence the score; if it contradicts or omits critical steps, reflect that in the score and reasoning.

Code description:
{code_description}
"""
    with dspy.context(lm=lm):
        response = qa(
            question=question,
            dataframe=dataframe_str,
            evaluation_criteria=extended_criteria
        )
    evaluation_json = extract_json_evaluation(response.evaluation)
    return evaluation_json.get("score", 0)

def evaluate_binary_dataframes(question, dataframes_list):  
    # Randomize presentation order to mitigate position bias
    pairs = [(0, dataframes_list[0]), (1, dataframes_list[1])]
    random.shuffle(pairs)
    order = [idx for idx, _ in pairs]
    df_1 = pairs[0][1]
    df_2 = pairs[1][1]
    with dspy.context(lm=lm):
        response = bi(
            question=question,
            dataframe_1=df_1,
            dataframe_2=df_2,
            evaluation_criteria=EVALUATION_BINARY_PROMPT
        )
    evaluation_data = json.loads(response.evaluation)
    presented_index = evaluation_data.get("best_index", 0)
    try:
        presented_index = int(presented_index)
    except Exception:
        presented_index = 0
    # Map selected index back to original indices
    original_index = order[presented_index]
    return original_index

def evaluate_binary_dataframes_with_confidence(question, dataframes_list):
    # Evaluate both permutations and use consensus or higher confidence to decide
    if not isinstance(dataframes_list, (list, tuple)) or len(dataframes_list) < 2:
        raise ValueError("dataframes_list must contain at least two items")

    # Randomize presentation order to mitigate position bias (same as evaluate_binary_dataframes)
    pairs = [(0, dataframes_list[0]), (1, dataframes_list[1])]
    random.shuffle(pairs)
    order = [idx for idx, _ in pairs]
    df_1 = pairs[0][1]
    df_2 = pairs[1][1]

    # Call 1: original order (A,B)
    order1 = order
    with dspy.context(lm=lm):
        resp1 = bi(
            question=question,
            dataframe_1=df_1,
            dataframe_2=df_2,
            evaluation_criteria=EVALUATION_BINARY_PROMPT
        )
    presented_index1, confidence1 = _parse_binary_evaluation(resp1.evaluation)
    original_index1 = order1[presented_index1] if presented_index1 in (0, 1) else 0

    # Call 2: swapped order (B,A)
    order2 = [order[1], order[0]]
    with dspy.context(lm=lm):
        resp2 = bi(
            question=question,
            dataframe_1=df_2,
            dataframe_2=df_1,
            evaluation_criteria=EVALUATION_BINARY_PROMPT 
        )
    presented_index2, confidence2 = _parse_binary_evaluation(resp2.evaluation)
    original_index2 = order2[presented_index2] if presented_index2 in (0, 1) else 0

    # If both picks coincide, return that
    if original_index1 == original_index2:
        return original_index1

    # Otherwise, choose the higher confidence
    if confidence1 > confidence2:
        return original_index1
    if confidence2 > confidence1:
        return original_index2

    # Tie-breaker: randomly choose one of the two original picks
    return random.choice([original_index1, original_index2])

def evaluate_binary_dataframes_with_pydough_confidence(question, dataframes_list, codes_list=None):
    """Binary evaluate two DataFrame candidates with optional PyDough code context.

    Args:
        question (str): The natural-language question to answer.
        dataframes_list (List[str]): Two JSON-serializable DataFrame renderings (as strings).
        codes_list (Optional[List[str]]): Optional list with two PyDough code strings aligned to dataframes_list.

    Returns:
        int: The index (0 or 1) of the better option in the ORIGINAL input order.
    """
    if not isinstance(dataframes_list, (list, tuple)) or len(dataframes_list) < 2:
        raise ValueError("dataframes_list must contain at least two items")

    codes_list = codes_list if isinstance(codes_list, (list, tuple)) else [None, None]
    if len(codes_list) < 2:
        # Pad to length 2 to simplify alignment logic
        codes_list = list(codes_list) + [None] * (2 - len(codes_list))

    def _canonical_code_text(txt):
        try:
            if txt is None:
                return "N/A"
            s = str(txt)
            # Light trimming to avoid overly long prompts
            max_chars = 4000
            return s[:max_chars]
        except Exception:
            return "N/A"

    # Randomize presentation order to mitigate position bias
    pairs = [(0, dataframes_list[0], codes_list[0]), (1, dataframes_list[1], codes_list[1])]
    random.shuffle(pairs)
    order = [idx for idx, _, _ in pairs]
    df_1, code_1 = pairs[0][1], pairs[0][2]
    df_2, code_2 = pairs[1][1], pairs[1][2]

    code_1_txt = _canonical_code_text(code_1)
    code_2_txt = _canonical_code_text(code_2)

    # Call 1: original randomized order (A,B)
    order1 = order
    with dspy.context(lm=lm):
        prompt1 = EVALUATION_BINARY_WITH_CODE_PROMPT_ARA.format(
            question=question,
            dataframe_1=df_1,
            dataframe_2=df_2,
            code_1=code_1_txt,
            code_2=code_2_txt,
        )
        resp1 = bi(
            question=question,
            dataframe_1=df_1,
            dataframe_2=df_2,
            evaluation_criteria=prompt1,
        )
    presented_index1, confidence1 = _parse_binary_evaluation(resp1.evaluation)
    original_index1 = order1[presented_index1] if presented_index1 in (0, 1) else 0

    # Call 2: swapped order (B,A) with corresponding code swapped
    order2 = [order[1], order[0]]
    with dspy.context(lm=lm):
        prompt2 = EVALUATION_BINARY_WITH_CODE_PROMPT_ARA.format(
            question=question,
            dataframe_1=df_2,
            dataframe_2=df_1,
            code_1=code_2_txt,
            code_2=code_1_txt,
        )
        resp2 = bi(
            question=question,
            dataframe_1=df_2,
            dataframe_2=df_1,
            evaluation_criteria=prompt2,
        )
    presented_index2, confidence2 = _parse_binary_evaluation(resp2.evaluation)
    original_index2 = order2[presented_index2] if presented_index2 in (0, 1) else 0

    # If both picks coincide, return that
    if original_index1 == original_index2:
        return original_index1

    # Otherwise, choose the higher confidence
    if confidence1 > confidence2:
        return original_index1
    if confidence2 > confidence1:
        return original_index2

    # Tie-breaker: randomly choose one of the two original picks
    return random.choice([original_index1, original_index2])

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
