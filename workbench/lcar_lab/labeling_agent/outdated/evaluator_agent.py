from typing import Dict, Any, List, Optional, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai.model_garden import ChatAnthropicVertex
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_core.prompts import PromptTemplate
from langchain.agents import initialize_agent, Tool, AgentExecutor
from langchain.agents.agent_types import AgentType
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
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
    # remove duplicate rows, if any
    df = df.drop_duplicates()

    # sort columns in alphabetical order of column names
    sorted_df = df.reindex(sorted(df.columns), axis=1)

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
        sorted_df = sorted_df.sort_values(by=list(sorted_df.columns))

    # reset index
    sorted_df = deduplicate_columns(sorted_df)
    sorted_df = sorted_df.reset_index(drop=True)
    return sorted_df

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
    # drop duplicates to ensure equivalence
    try:
        if df_gold.equals(df_gen):
            return True
    except:
        pass

    df_gold = normalize_table(df_gold, query_category, question, query_gold)
    df_gen = normalize_table(df_gen, query_category, question, query_gen)

    # perform same checks again for normalized tables
    if df_gold.shape != df_gen.shape:
        return False
    # fill NaNs with -99999 to handle NaNs in the dataframes for comparison
    df_gen.fillna(-99999, inplace=True)
    df_gold.fillna(-99999, inplace=True)
    
    is_equal = df_gold.values == df_gen.values
    try:
        return is_equal.all()
    except:
        return is_equal
    
class SQLEvaluatorAgent:
    def __init__(self, db_connection_string: str, cheatsheet_path: str):
        """Initialize the SQL evaluator agent with a database connection."""
        self.db = SQLDatabase.from_uri(db_connection_string)

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0
        )

        # gemini-2.5-flash-preview-04-17
        # gemini-2.0-flash

        """ self.llm = ChatAnthropicVertex(
            model_name="claude-3-7-sonnet@20250219",
            project="solid-drive-448717-p8",
            location="us-east5",
        ) """

        self.cheatsheet_path = cheatsheet_path
        
        # Create a simple tool that returns the precomputed match
        self.match_tool = Tool(
            name="get_match_result",
            func=lambda x: x,  # Just returns the input
            description="Returns the precomputed match result between ground truth and generated response."
        )
        
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
        # Create a ReAct-style prompt template
        prompt = PromptTemplate(
            input_variables=["input"],
            template="""
You are an expert database evaluator agent. Your task is to evaluate if a generated response correctly answers a question based on ground truth SQL results.

You have access to the following information:
- The original question being answered
- The ground truth SQL query and its results
- The generated response writen in Pydough syntax, which is similar bit not the same as SQL. 
- The output dataframes of both the SQL execution and Pydough execution (when available).
- A precomputed boolean indicating if the ground truth vs generated dataframes match.

Your task is to:
1. Analyze the ground truth results and the generated response
2. Consider the precomputed dataframe match result
3. Make a final judgment about whether the responses match
4. If they don't match, provide detailed feedback about what went wrong and how to fix it

Question: {input}

Thought: I should analyze the results and provide a clear evaluation.
Action: get_match_result
Action Input: The precomputed match result
Observation: The match result is available
Final Answer:
"""
        )
        
        # Build the agent with the match tool
        agent = initialize_agent(
            tools=[self.match_tool],
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            prompt=prompt,
            verbose=True
        )
        
        return agent
    
    def evaluate_responses(self, question: str, ground_truth_sql: str, generated_response: str, generated_df_json: str = None, precomputed_match: bool = None) -> Dict[str, Any]:
        """Evaluate if the generated response correctly answers the question based on ground truth SQL.
        
        Args:
            question: The original question being answered
            ground_truth_sql: The ground truth SQL query
            generated_response: The text response from the generator agent
            generated_df_json: The JSON string representation of the generated DataFrame (optional)
            precomputed_match: Precomputed boolean result of DataFrame comparison (optional)
        """
        # Convert SQL result to DataFrame JSON
        ground_truth_json = self._convert_sql_to_dataframe(ground_truth_sql)
        
        with open(self.cheatsheet_path, 'r', encoding='utf-8') as f:
            cheatsheet_content = f.read()

        # If generated_df_json is provided, use it directly
        if generated_df_json:
            generated_json = generated_df_json
        else:
            generated_json = "{}"
            
        # Create input for the ReAct agent
        agent_input = f"""Evaluate if the following generated response correctly answers the question and provide feedback:

User Question: {question}

Ground Truth SQL: {ground_truth_sql}

Generated Response: {generated_response}

The ground truth DataFrame (as JSON) is:
{ground_truth_json}

The generated response DataFrame (as JSON) is:
{generated_json}

Direct Full DataFrame Numerical Comparison Result (ground truth vs generated response): {'True' if precomputed_match else 'False' if precomputed_match is not None else 'Not provided'}

Response Guidelines: 

1. If the generated response matches the ground truth, return True. If it does not, return a brief explanation of what went wrong and how it could be fixed. 
2. When providing feedback be specific and detailed as to what is not matching with the ground truth.
3. The generated response is executed using Pydough syntax, not SQL.
4. We are aiming to provide actionable feedback to help generate better Pydough.
5. Do not generate any code. Provide feedback only in plain english when applicable.
6. Provided dataframes can be samples if sized 50 rows as original are too large.
7. Provide sufficient information in the final answer to be actionable and generate better responses from the Pydough generator. 
8. 5. If this is a Pydough issue, please check the cheatsheet below for Pydough syntax and provide feedback on how to fix it.
{cheatsheet_content}
"""
        
        # Run the ReAct agent
        result = self.agent.run(agent_input)
        
        # Parse the result
        match = "True" in result
        explanation = result
        
        return {
            "match": match,
            "explanation": explanation,
            "ground_truth_result": ground_truth_json,
            "ground_truth_response": self.generate_response_from_sql(question, ground_truth_json),
            "generated_response": generated_response,
            "generated_df_json": generated_json
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
        # print(f"Error: Database file not found at {db_path}")
        # print("Please ensure the database file exists at the specified path.")
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
            model="gemini-2.0-flash",
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
            template="""
You are an expert database evaluator agent. Your task is to evaluate if a generated response correctly answers a question based on ground truth SQL results.

You have access to the following information:
- The original question being answered
- The ground truth SQL query and its results
- The generated response writen in Pydough syntax, which is similar bit not the same as SQL. 
- The output dataframes of both the SQL execution and Pydough execution (when available).
- A precomputed boolean indicating if the ground truth vs generated dataframes match.

Your task is to:
1. Analyze the ground truth results and the generated response
2. Consider the precomputed dataframe match result
3. Make a final judgment about whether the responses match
4. If they don't match, provide detailed feedback about what went wrong and how to fix it

Question: {input}

Thought: I should analyze the results and provide a clear evaluation.
Action: get_match_result
Action Input: The precomputed match result
Observation: The match result is available
Final Answer:
"""
        )
        # print("ReAct prompt template created successfully")
        
        # print("\nInitializing ReAct agent...")
        agent = initialize_agent(
            tools=[df_comparison_tool],
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            prompt=prompt,
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