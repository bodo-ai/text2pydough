from typing import Dict, Any, List, Optional, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai.model_garden import ChatAnthropicVertex
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_core.prompts import PromptTemplate
from langchain.agents import initialize_agent, Tool, AgentExecutor, ZeroShotAgent
from langchain.agents.agent_types import AgentType
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.chains import LLMChain
import pandas as pd
import re
import collections
from io import StringIO
import os
import numpy as np
import json
import re
from io import StringIO
from tqdm import tqdm
import mlflow
import logging
from pandas.api.types import is_numeric_dtype

# Global variable to control logging backend

# USE_MLFLOW = True  # Set to False to use Phoenix instead
# # Configure MLflow
# if USE_MLFLOW:
#     MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
#     MLFLOW_TRACKING_TOKEN = os.getenv("MLFLOW_TRACKING_TOKEN", "")
#     # print(MLFLOW_TRACKING_URI)
#     mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
#     mlflow.set_experiment(os.getenv("EXPERIMENT_NAME", "agent-playground"))
#     # Enable MLflow LangChain autologging
#     mlflow.langchain.autolog(
#         log_traces=True,
#         log_models=True,
#         log_input_examples=True,
#         log_model_signatures=True,
#         registered_model_name="pydough_agent"
#     )
# else:
#     # Register a Phoenix tracer
#     from phoenix.otel import register
#     API_KEY = os.getenv("PHOENIX_API_KEY")
#     COLLECTOR_ENDPOINT = os.getenv("PHOENIX_COLLECTOR_ENDPOINT")  # Ej: "http://mlflow-alb-1071096006.us-east-2.elb.amazonaws.com:6060/v1/traces"
#     tracer_provider = register(
#         endpoint=COLLECTOR_ENDPOINT,               # URL raíz sin /v1/traces
#         headers={"Authorization": f"Bearer {API_KEY}"},
#         project_name=os.getenv("EXPERIMENT_NAME", "agent-react-testing"),
#         auto_instrument=True,
#         protocol="http/protobuf"                    # Forzar uso HTTP en lugar de gRPC
#     )

def _clean_mixed_column(series: pd.Series) -> pd.Series:
    """
    Clean a single column with mixed data types.
    
    Strategy:
    1. Try to convert to numeric (handles strings like '45.3')
    2. Replace empty strings and whitespace with NaN
    3. If mostly numeric, keep as numeric; otherwise keep as cleaned strings
    """
    # First, standardize empty/whitespace values to NaN
    cleaned_series = series
    
    # Replace empty strings, whitespace, and common null representations
    null_representations = ['', ' ', 'null', 'NULL', 'None', 'nan', 'NaN', 'n/a', 'N/A']
    cleaned_series = cleaned_series.replace(null_representations, pd.NA)
    
    # Try to convert to numeric
    numeric_series = pd.to_numeric(cleaned_series, errors='coerce')
    
    # Count how many values successfully converted to numeric
    non_null_original = cleaned_series.notna().sum()
    non_null_numeric = numeric_series.notna().sum()
    
    # If most values (>80%) are numeric, use numeric version
    if non_null_original > 0 and (non_null_numeric / non_null_original) > 0.8:
        return numeric_series
    else:
        # Keep as cleaned strings, but ensure consistent string representation
        return cleaned_series.astype(str).replace(['nan', 'None', '<NA>'], pd.NA)
    
def _clean_mixed_type_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean columns with mixed data types (e.g., numeric values mixed with empty strings).
    
    This handles common data quality issues like:
    - Numeric columns with empty strings or whitespace
    - Mixed numeric/string data
    - Various representations of missing values
    """
    cleaned_df = df
    
    for col in cleaned_df.columns:
        if cleaned_df[col].dtype == 'object':
            # Convert the column to handle mixed types
            cleaned_df[col] = _clean_mixed_column(cleaned_df[col])
    
    return cleaned_df

def _sort_by_all_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Sort dataframe by all columns with proper error handling for mixed types."""
    try:
        # Clean mixed-type columns before sorting
        cleaned_df = _clean_mixed_type_columns(df)
        return cleaned_df.sort_values(
            by=list(cleaned_df.columns), 
            ascending=True,
            na_position='last'
        )
    except Exception as e:
        logging.warning(f"Failed to sort by all columns: {e}. Returning unsorted dataframe.")
        return df
    
def deduplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = df.columns.tolist()
    if len(cols) != len(set(cols)):
        duplicates = [
            item for item, count in collections.Counter(cols).items() if count > 1
        ]
        for dup in duplicates:
            indices = [i for i, x in enumerate(cols) if x == dup]
            for i in indices:
                cols[i] = f"{dup}_{i}"
        df.columns = cols
    return df

def normalize_table(
    df: pd.DataFrame, query_category: str, question: str, sql: str = None
) -> pd.DataFrame:
    """
    Normalizes a dataframe by:
    1. removing all duplicate rows
    2. sorting columns in alphabetical order
    3. sorting rows using values from first column to last (if query_category is not 'order_by' and question does not ask for ordering)
    4. resetting index
    """
    
    # sort columns in alphabetical order of column names
    df = deduplicate_columns(df)  # remove duplicate columns
    
    sorted_df = df.reset_index(drop=True).reindex(sorted(df.columns), axis=1)

    # check if query_category is 'order_by' and if question asks for ordering
    has_order_by = False
    pattern = re.compile(r"\b(order|sort|arrange)\b", re.IGNORECASE)
    in_question = re.search(pattern, question.lower())  # true if contains
    if query_category == "order_by" or in_question:
        has_order_by = True

        if sql:
            # determine which columns are in the ORDER BY clause of the sql generated, using regex
            pattern = re.compile(r"ORDER BY[\s\S]*", re.IGNORECASE)
            order_by_clause = re.search(pattern, sql)
            if order_by_clause:
                order_by_clause = order_by_clause.group(0)
                # get all columns in the ORDER BY clause, by looking at the text between ORDER BY and the next semicolon, comma, or parantheses
                pattern = re.compile(r"(?<=ORDER BY)(.*?)(?=;|,|\)|$)", re.IGNORECASE)
                order_by_columns = re.findall(pattern, order_by_clause)
                order_by_columns = (
                    order_by_columns[0].split() if order_by_columns else []
                )
                order_by_columns = [
                    col.strip().rsplit(".", 1)[-1] for col in order_by_columns
                ]

                ascending = False
                # if there is a DESC or ASC in the ORDER BY clause, set the ascending to that
                if "DESC" in [i.upper() for i in order_by_columns]:
                    ascending = False
                elif "ASC" in [i.upper() for i in order_by_columns]:
                    ascending = True

                # remove whitespace, commas, and parantheses
                order_by_columns = [col.strip() for col in order_by_columns]
                order_by_columns = [
                    col.replace(",", "").replace("(", "") for col in order_by_columns
                ]
                order_by_columns = [
                    i
                    for i in order_by_columns
                    if i.lower()
                    not in ["desc", "asc", "nulls", "last", "first", "limit"]
                ]

                # get all columns in sorted_df that are not in order_by_columns
                other_columns = [
                    i for i in sorted_df.columns.tolist() if i not in order_by_columns
                ]

                # only choose order_by_columns that are in sorted_df
                order_by_columns = [
                    i for i in order_by_columns if i in sorted_df.columns.tolist()
                ]
                sorted_df = sorted_df.sort_values(
                    by=order_by_columns + other_columns, ascending=ascending
                )

                sorted_df = sorted_df[other_columns + order_by_columns]

    if not has_order_by:
        # sort rows using values from first column to last
        sorted_df = _sort_by_all_columns(sorted_df)

    # reset index
    sorted_df = sorted_df.reset_index(drop=True)

    return sorted_df

def series_match(s_gold: pd.Series, s_gen: pd.Series, numeric_tolerance = 1e-5) -> bool:
    """
    Checks if two Series have identical dtypes and values in the same order.
    Their original indices/names are ignored for the comparison itself, but they must
    have the same length (which should be pre-checked at the DataFrame level).
    """

    if is_numeric_dtype(s_gold) and is_numeric_dtype(s_gen):
        
        # If gold series is bigger than generated series, they cannot be equal
        if len(s_gold) > len(s_gen):
            return False
        # Check if the numeric values are equal within a small tolerance
        float_gold = pd.to_numeric(s_gold, errors='coerce').reset_index(drop=True)
        float_gen = pd.to_numeric(s_gen, errors='coerce').reset_index(drop=True)
        '''
        if float_gold.isin(float_gen).all():
            print("Info: Numeric series contents Match. LENIENT")
            return True
        '''
        # If they are not equal, check if they are within the numeric tolerance
        for i in range(len(float_gold)):
            if not (abs(float_gold[i] - float_gen[i]) < numeric_tolerance):
                #print(f"Info: Numeric series contents differ at index {i}: {float_gold[i]} vs {float_gen[i]}")
                return False
        #print("Info: Numeric series contents Match.")
        return True
    # If they are not numeric, check if they are equal directly
    reset_gold = s_gold.reset_index(drop=True)
    reset_gen = s_gen.reset_index(drop=True)
    if reset_gold.dtype != reset_gen.dtype:
        return False
    if reset_gold.isin(reset_gen).all():
        #print("Info: Series contents Match.")
        return True
    else:
        #print("Info: Series contents do not Match.")
        return False

def secondary_check(df_gold: pd.DataFrame, df_gen: pd.DataFrame) -> bool:
    """
    Checks if all column contents of DataFrame A can be uniquely matched to column
    contents in DataFrame B. Column names and the order of columns in both
    DataFrames are ignored. Only dtype and values (in order) within each column matter.

    Args:
        df_gold (pd.DataFrame): The dataframe obtained by running the reference SQL.
        df_gen (pd.DataFrame): The dataframe obtained by running the generated PyDough code.

    Returns:
        bool: True if all column contents of df_gold can be uniquely matched in df_gen, False otherwise.
    """
    num_gold_cols = df_gold.shape[1]
    num_gen_cols = df_gen.shape[1]
    num_gold_rows = df_gold.shape[0]
    num_gen_rows = df_gen.shape[0]

    # 1. Handle df_gold having zero columns
    if num_gold_cols == 0:
        if num_gold_rows == 0: # df_gold is 0x0
            #print("Info: df_gold has 0 columns and 0 rows. Trivially True.")
            return True
        else: # df_gold is Rx0 (R > 0)
            # For "exact values" across 0 columns but R rows, df_gen must also have R rows.
            result = num_gold_rows == num_gen_rows
            return result

    # 2. Not enough columns in df_gen to match all of df_gold's columns
    if num_gold_cols > num_gen_cols:
        #print(f"Info: Not enough columns in df_gen to match all of df_gold's columns: {num_gold_cols} vs {num_gen_cols}.")
        return False
    
    if num_gold_rows > num_gen_rows:
        #print(f"Info: Not enough rows in df_gen to match all of df_gold's rows: {num_gold_rows} vs {num_gen_rows}.")
        return False
    
    # --- Greedy Matching ---
    b_cols_used = [False] * num_gen_cols # Tracks which columns in df_gen have been matched

    #print(f"Info: Starting greedy matching")
    for i in range(num_gold_cols):
        series_gold = df_gold.iloc[:, i]
        found_match_for_s_gold = False
        for j in range(num_gen_cols):
            if not b_cols_used[j]: # If df_gen's j-th column is not yet used
                series_gen = df_gen.iloc[:, j]
                #print(f"Info: Comparing column {i} of df_gold with column {j} of df_gen.")
                if series_match(series_gold, series_gen):
                    b_cols_used[j] = True
                    found_match_for_s_gold = True
                    break # Move to the next column in df_gold
        
        if not found_match_for_s_gold:
            #print(f"Info: No match found for column {i} of df_gold in df_gen.")
            return False
    print("Info: Dataframes match second check.")    
    return True    

def compare_df(
    df_gold: pd.DataFrame,
    df_gen: pd.DataFrame,
    query_category: str,
    question: str,
    query_gold: str = None,
    query_gen: str = None,
) -> bool:
    """
    Compares two dataframes and returns True if they are the same, else False.
    query_gold and query_gen are the original queries that generated the respective dataframes.
    """
    
    #print(f"Info: Comparing DataFrames for question: {question}")
    original_gold = df_gold.copy()
    original_gen = df_gen.copy()
    try:
        is_equal = df_gold.values == df_gen.values
        if is_equal.all():
            return True
    except:
        try:
            is_equal = df_gold.values == df_gen.values
            if is_equal:
                return True
        except:
            pass

    df_gold = normalize_table(df_gold, query_category, question, query_gold)
    df_gen = normalize_table(df_gen, query_category, question, query_gen)

    # fill NaNs with -99999 to handle NaNs in the dataframes for comparison
    df_gold.fillna(-99999, inplace=True)
    df_gen.fillna(-99999, inplace=True)
    
    try:
        #print("Info: Comparing DataFrames using hard match.")
        is_equal = df_gold.values == df_gen.values
        if is_equal.all():
            #print("Info: DataFrames match first check.")
            return True
    except:
        try:
            is_equal = df_gold.values == df_gen.values
            if is_equal:
                return True
        except:
            pass
    #print("Info: Proceeding with secondary check.")
    return secondary_check(original_gold, original_gen)
    
class MatchTool(BaseTool):
    name: str = "get_match_result"
    description: str = "Returns True if dataframes match, else False."
    
    def __init__(self, match_result: bool):
        super().__init__()
        self._match_result = match_result
    
    def _run(self, *args, **kwargs) -> str:
        return json.dumps({"match": self._match_result})
    
    def _arun(self, *args, **kwargs) -> str:
        raise NotImplementedError("Async operation not supported")

class SQLEvaluatorAgent:
    def __init__(self, db_connection_string: str):
        """Initialize the SQL evaluator agent with a database connection."""
        self.db = SQLDatabase.from_uri(db_connection_string)
        
        self.llm = ChatGoogleGenerativeAI(
           model="gemini-2.5-flash-preview-05-20",
           temperature=0
        )

        #self.llm = ChatAnthropicVertex(
        #     model_name="claude-sonnet-4@20250514",
        #     project="solid-drive-448717-p8",
        #     location="us-east5"
        #)
        
        # Create SQL toolkit for database operations
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        
        # Create the ReAct agent
        self.agent = self._create_react_agent()
    
    def _convert_sql_to_dataframe(self, sql_query: str) -> str:
        """Execute SQL query and return results as a JSON string."""
        try:
            # print(f"\nExecuting SQL query: {sql_query}")
            
            # Get the SQLAlchemy engine from the database
            engine = getattr(self.db, "engine", None) or self.db._engine
            
            # Use pandas to directly read the SQL query
            df = pd.read_sql_query(sql_query, engine)
            
            # print(f"Successfully converted to DataFrame with shape: {df.shape}")
            # print(f"DataFrame columns: {df.columns.tolist()}")
            # print(f"First few rows:\n{df.head()}")
            
            # Convert to JSON string using default to_json()
            json_str = df.to_json(orient='records')
            # print(f"Converted to JSON string of length: {len(json_str)}")
            # print(f"JSON string preview: {json_str[:200]}...")  # Show first 200 characters
            return json_str
            
        except Exception as e:
            # print(f"Error executing SQL query: {str(e)}")
            # print("\nDetailed error information:")
            # import traceback
            # traceback.print_exc()
            return "{}"  # Return empty JSON object instead of array
    
    def _convert_text_to_dataframe(self, text: str) -> str:
        """Convert text response to DataFrame JSON string."""
        try:
            # If the text is already a JSON string, use it directly
            if text.startswith('[') or text.startswith('{'):
                try:
                    # Try to parse as JSON first to validate
                    json.loads(text)
                    return text
                except json.JSONDecodeError:
                    pass
            
            # If not a valid JSON string, try to convert using pd.read_json
            try:
                # Try to read as JSON string
                df = pd.read_json(StringIO(text))
                return df.to_json(orient='records')
            except:
                # If that fails, return empty JSON array
                return "[]"
            
        except Exception as e:
            # print(f"Error converting text to DataFrame: {str(e)}")
            # print("\nDetailed error information:")
            # import traceback
            # traceback.print_exc()
            return "[]"  # Return empty JSON array
    
    def _compare_dataframes_wrapper(self, input_dict: Dict[str, Any]) -> bool:
        """Wrapper function to handle DataFrame comparison with JSON strings."""
        try:
            # 1) if you got a JSON string, load it; otherwise assume dict already
            if isinstance(input_dict, str):
                input_dict_json = json.loads(input_dict)
                # print("\nEVALUATOR:JSON Converted!\n")
                # print(input_dict_json)
            # 2) re-dump to a JSON text blob
            raw1 = json.dumps(input_dict_json["df1"])
            raw2 = json.dumps(input_dict_json["df2"])

            # 3) read it back into pandas (auto-detects orient)
            df1 = pd.read_json(StringIO(raw1))
            df2 = pd.read_json(StringIO(raw2))
            
            # print("\nDF1\n")
            # print(df1)
            # print("\nDF2\n")
            # print(df2)
            
            # Compare DataFrames
            return compare_df(
                df1,
                df2,
                input_dict["query_category"],
                input_dict["question"]
            )
        except Exception as e:
            # print(f"\nEVALUATOR: Error comparing DataFrames: {str(e)}\n")
            # print(type(input_dict))
            # print(input_dict)
            return False
    
    def _create_react_agent(self):
        """Create a ReAct agent with the necessary tools and prompt template."""
        # Get all tools from the SQL toolkit
        sql_tools = self.toolkit.get_tools()
        
        # Create a ReAct-style prompt template
        prompt = PromptTemplate(
            input_variables=["input", "agent_scratchpad"],
            template="""You are an expert database evaluator agent. 
Your task is to evaluate if a generated Pydough response correctly answers a question based on ground truth SQL results.
Your feedback in the final explanation must be actionable so that the generator can fix the issue. Describe the issues in detail.
Use the tools provided to help diagnose issues and provide better feedback.

You have access to the following tools:
- sql_db_list_tables: List all tables in the database
- sql_db_schema: Get the schema of specific tables
- sql_db_query_checker: Check if a SQL query is valid
- sql_db_query: Execute a SQL query

Your task is to:
1. Analyze the ground truth results and the generated response
2. Consider the precomputed dataframe numerical match result
3. Make a final judgment about whether the responses match
4. If they don't match, provide detailed feedback about what went wrong and how to fix it

You MUST follow this exact format for each step, with NO blank lines between the required keys:

Thought: (your reasoning about what to do next)
Action: (must be one of [sql_db_list_tables, sql_db_schema, sql_db_query_checker, sql_db_query])
Action Input: (the input to the action)
Observation: (the result of the action)

After every Thought: you MUST output Action: and Action Input: on the very next lines.
Do not insert blank lines between the required keys.
You MUST include ALL three parts (Thought, Action, Action Input) for each step, except the final answer.
You MUST use only one of the listed tools for each Action.
You MUST wait for the Observation before proceeding to the next step.

When you have enough information and need no further tool calls, output EXACTLY this format:
Final Answer: {{"match": false, "explanation": "your explanation here"}}

The match value MUST be a boolean (true or false).
The explanation MUST be a string explaining your reasoning.
Do NOT output 'Action: N/A'. Do NOT invent tool names.
Do NOT add any text before or after the Final Answer JSON.

Begin!

Question: {input}

{agent_scratchpad}"""
        )
        
        # Create the LLM chain
        llm_chain = LLMChain(llm=self.llm, prompt=prompt)
        
        # Build the custom ReAct-style agent manually
        react_agent = ZeroShotAgent(
            llm_chain=llm_chain,
            tools=sql_tools,
            verbose=True,
            handle_parsing_errors=True
        )

        # Wrap in AgentExecutor with proper configuration
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=react_agent,
            tools=sql_tools,
            return_intermediate_steps=True,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=30
        )
        
        return agent_executor
    
    def evaluate_responses(self, question: str, ground_truth_sql: str, generated_response: str, generated_df_json: str = None, precomputed_match: bool = None, executor_error: str = None) -> Dict[str, Any]:
        """Evaluate if the generated response correctly answers the question based on ground truth SQL.
        
        Args:
            question: The original question being answered
            ground_truth_sql: The ground truth SQL query
            generated_response: The text response from the generator agent
            generated_df_json: The JSON string representation of the generated DataFrame (optional)
            precomputed_match: Precomputed boolean result of DataFrame comparison (optional)
            executor_error: Error message from the executor if any (optional)
        """
        # Convert SQL result to DataFrame JSON
        ground_truth_json = self._convert_sql_to_dataframe(ground_truth_sql)
        
        # If generated_df_json is provided, use it directly
        if generated_df_json:
            generated_json = generated_df_json
        else:
            generated_json = "{}"
            
        # Create the match tool with the precomputed result
        match_tool = MatchTool(precomputed_match)
        
        # Create a new agent with the match tool
        self.agent = self._create_react_agent()
        self.agent.tools.append(match_tool)
            
        # Create input for the ReAct agent
        agent_input = f"""Evaluate if the following generated response correctly answers the question:

User Question: {question}

Ground Truth SQL: {ground_truth_sql}

Generated Response: {generated_response}

ResponseGuidelines: 

1. If the generated response matches the ground truth, return True. If it does not, return a brief explanation of what went wrong and how it could be fixed. 
2. When providing feedback be specific and detailed as to what is not matching with the ground truth.
3. The generated response is executed using Pydough syntax, not SQL.
4. We are aiming to provide actionable feedback to help generate better Pydough.
5. Do not generate any code. Provide feedback only in plain english when applicable.
6. Provided dataframes can be only samples if sized 20 rows as original are too large.

DataFrame Comparison Result: {precomputed_match}

The ground truth DataFrame (as JSON) is:
{ground_truth_json}

The generated response DataFrame (as JSON) is:
{generated_json}"""

        if executor_error:
            agent_input += f"\nPydough Executor Error: {executor_error}"
            print(f"\nExecutor Error: {executor_error}")
        
        try:
            # Run the ReAct agent and get intermediate steps
            output = self.agent.invoke({
                "input": agent_input,
                "agent_scratchpad": ""
            })
            final_answer = output["output"]
            intermediate_steps = output["intermediate_steps"]
            
            # Parse the result
            try:
                # Extract the JSON part from the final answer
                json_str = final_answer.split("Final Answer:")[-1].strip()
                # Remove any leading/trailing whitespace or newlines
                json_str = json_str.strip()
                # Ensure we have a valid JSON string
                if not json_str.startswith("{") or not json_str.endswith("}"):
                    raise ValueError("Invalid JSON format in agent output")
                result_dict = json.loads(json_str)
                if "match" not in result_dict or "explanation" not in result_dict:
                    raise ValueError("Missing required keys in agent output")
                match = result_dict["match"]
                explanation = result_dict["explanation"]
            except Exception as e:
                # Check for iteration or time limit error
                if "Agent stopped due to iteration limit or time limit." in final_answer:
                    print("Error: Agent exceeded iteration or time limit.")
                    match = False
                    explanation = (
                        "The agent stopped because it exceeded the iteration or time limit. "
                        "Consider simplifying the input question or increasing the limits if appropriate."
                    )
                else:
                    print(f"Error parsing agent output: {str(e)}")
                    print(f"Raw output: {final_answer}")
                    match = False
                    explanation = f"Error parsing agent output: {str(e)}"
            
            return {
                "match": match,
                "explanation": explanation,
                "ground_truth_result": ground_truth_json,
                "ground_truth_response": self.generate_response_from_sql(question, ground_truth_json),
                "generated_response": generated_response,
                "generated_df_json": generated_json,
                "intermediate_steps": intermediate_steps
            }
        except Exception as e:
            error_message = str(e)
            explanation = f"Error in agent execution: {error_message}"
            print(f"Error in agent execution: {explanation}")
            
            return {
                "match": False,
                "explanation": explanation,
                "ground_truth_result": ground_truth_json,
                "ground_truth_response": self.generate_response_from_sql(question, ground_truth_json),
                "generated_response": generated_response,
                "generated_df_json": generated_json,
                "intermediate_steps": []
            }

    
    def generate_response_from_sql(self, question: str, sql_results: str) -> str:
        """Generate a natural language response based on the question and SQL results."""
        prompt = f"""Given the following question and SQL query results, generate a clear and concise answer:

Question: {question}

SQL Query Results:
{sql_results}

Please provide a direct answer to the question using the information from the SQL results.
The answer should be in natural language and directly address the question."""
        
        response = self.llm.invoke(prompt)
        #print("\nRESPONSE\n")
        #print(response.content)
        return response.content

def main():
    # Database path - handle both Windows and WSL paths
    if os.path.exists("/mnt/c"):
        # WSL environment
        db_path = "/mnt/c/Users/david/bodo/TPCH/test_data/tpch.db"
    else:
        # Windows environment
        db_path = os.path.join("C:", "Users", "david", "bodo", "TPCH", "test_data", "tpch.db")
    
    # Verify database exists
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        print("Please ensure the database file exists at the specified path.")
        return

    db_connection_string = f"sqlite:///{db_path}"
    # print(f"Using database at: {db_path}")

    # Initialize the evaluator with detailed error handling
    try:
        # print("\nInitializing SQL Database connection...")
        db = SQLDatabase.from_uri(db_connection_string)
        # print("SQL Database connection successful")
        
        # print("\nInitializing LLM...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",#"gemini-2.5-flash-preview-04-17",
            temperature=0
        )
        # print("LLM initialization successful")
        
        # print("\nCreating DataFrame comparison tool...")
        df_comparison_tool = Tool(
            name="compare_dataframes",
            func=lambda df1, df2, query_category, question: compare_df(df1, df2, query_category, question),
            description="""Compares two pandas DataFrames for numerical equivalence.
            Input should be a dictionary with keys:
            - df1: First DataFrame (Ground Truth)
            - df2: Second DataFrame (Generated)
            - query_category: Category of the query (e.g., 'order_by')
            - question: Original question being answered
            
            Returns True if the DataFrames are equivalent, False otherwise."""
        )
        # print("DataFrame comparison tool created successfully")
        
        # print("\nCreating ReAct prompt template...")
        prompt = PromptTemplate(
            input_variables=["input"],
            template="""You are an expert database evaluator agent. Your task is to evaluate if a generated response correctly answers a question based on ground truth SQL results.

You have access to the following tools:
- sql_db_list_tables: List all tables in the database
- sql_db_schema: Get the schema of specific tables
- sql_db_query_checker: Check if a SQL query is valid
- sql_db_query: Execute a SQL query
- get_match_result: Returns True if dataframes match, else False

Your task is to:
1. Analyze the ground truth results and the generated response
2. Consider the precomputed dataframe match result
3. Make a final judgment about whether the responses match
4. If they don't match, provide detailed feedback about what went wrong and how to fix it

You MUST follow this exact format for each step, with NO blank lines between the required keys:

Thought: (your reasoning about what to do next)
Action: (must be one of [sql_db_list_tables, sql_db_schema, sql_db_query_checker, sql_db_query, get_match_result])
Action Input: (the input to the action)
Observation: (the result of the action)

After every Thought: you MUST output Action: and Action Input: on the very next lines.
Do not insert blank lines between the required keys.
You MUST include ALL three parts (Thought, Action, Action Input) for each step.
You MUST use one of the listed tools for each Action.
You MUST wait for the Observation before proceeding to the next step.

When you have enough information and need no further tool calls, output EXACTLY this format:
Final Answer: {{"match": true, "explanation": "your explanation here"}}

The match value MUST be a boolean (true or false).
The explanation MUST be a string explaining your reasoning.
Do NOT output 'Action: N/A'. Do NOT invent tool names.

Begin!

Question: {input}"""
        )
        # print("ReAct prompt template created successfully")
        
        # print("\nInitializing ReAct agent...")
        agent = initialize_agent(
            tools=[df_comparison_tool],
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            prompt=prompt,
            return_intermediate_steps=True,
            verbose=True
        )
        # print("ReAct agent initialized successfully")
        
        evaluator = SQLEvaluatorAgent(db_connection_string)
        # print("Evaluator agent created successfully")
        
    except Exception as e:
        # print(f"\nError during initialization: {str(e)}")
        # print("\nDetailed error information:")
        # import traceback
        # traceback.print_exc()
        return

    # Test case: Customer and Supplier Count by Nation
    # print("\nTest Case: Customer and Supplier Count by Nation")
    question = "List the total number of customers and suppliers in each nation. Order by nation name"
    ground_truth_sql = "SELECT n_name AS nation_name, COUNT(DISTINCT c_custkey) AS total_customers, COUNT(DISTINCT s_suppkey) AS total_suppliers FROM nation LEFT JOIN customer ON n_nationkey = c_nationkey LEFT JOIN supplier ON n_nationkey = s_nationkey GROUP BY n_name;"
    
    # Create a random DataFrame for testing
    nations = ['Algeria', 'Argentina', 'Brazil', 'Canada', 'Egypt', 'Ethiopia', 'France', 'Germany', 
               'India', 'Indonesia', 'Iran', 'Iraq', 'Japan', 'Jordan', 'Kenya', 'Morocco', 
               'Mozambique', 'Peru', 'China', 'Romania', 'Saudi Arabia', 'Vietnam', 'Russia', 
               'United Kingdom', 'United States']
    
    # Generate random customer and supplier counts
    np.random.seed(42)  # For reproducibility
    customers = np.random.randint(1, 4, size=len(nations))
    suppliers = np.random.randint(2, 5, size=len(nations))
    
    # Create the DataFrame
    generated_df = pd.DataFrame({
        'nation_name': nations,
        'total_customers': customers,
        'total_suppliers': suppliers
    })
    
    # Sort by nation name
    generated_df = generated_df.sort_values('nation_name')
    
    # Convert DataFrame to JSON string
    generated_df_json = generated_df.to_json(orient='records')
    
    # Create a text response for the generator
    generated_response = "Here is the analysis of customers and suppliers by nation:\n\n"
    for _, row in generated_df.iterrows():
        generated_response += f"{row['nation_name']}: {row['total_customers']} customers, {row['total_suppliers']} suppliers\n"
    generated_response += "\nThe results are ordered by nation name as requested."

    # Run the evaluation
    # print("\nRunning evaluation...")
    try:
        result = evaluator.evaluate_responses(
            question=question,
            ground_truth_sql=ground_truth_sql,
            generated_response=generated_response,
            generated_df_json=generated_df_json
        )
        
        # Print results
        # print("\nEvaluation Results:")
        # print(f"Match: {result['match']}")
        # print(f"Explanation: {result['explanation']}")
        # print("\nGround Truth SQL Results:")
        # print(result['ground_truth_result'])
        # print("\nGround Truth Response:")
        # print(result['ground_truth_response'])
        # print("\nGenerated Response:")
        # print(result['generated_response'])
        # print("\nGenerated DataFrame JSON:")
        # print(result['generated_df_json'])
    except Exception as e:
        # print(f"\nError during evaluation: {str(e)}")
        # print("\nDetailed error information:")
        # import traceback
        # traceback.print_exc()
        pass

if __name__ == "__main__":
    main() 