from typing import List, Dict, Any, Union, Optional, Tuple
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool, BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from sqlalchemy import create_engine, text, inspect
import pandas as pd
import os
from dotenv import load_dotenv
from tqdm import tqdm
import argparse
import pydough  # External package
from datetime import datetime
from pydough_data.eval import execute_code_and_extract_result  # Local module
import json
import collections
import re
from concurrent.futures import ThreadPoolExecutor
from pydough.unqualified import transform_cell
from pydantic import Field

pydough.active_session.load_metadata_graph("/mnt/c/Users/david/bodo/TPCH/test_data/tpch_demo_graph.json", "TPCH")
pydough.active_session.connect_database("sqlite", database="/mnt/c/Users/david/bodo/TPCH/test_data/tpch.db",  check_same_thread=False)

load_dotenv()

# Mapping of SQLite types to PyDough types
SQLITE_TYPE_MAP = {
    "INTEGER": "int64",
    "INT": "int64",
    "BIGINT": "int64",
    "TINYINT": "int64",
    "SMALLINT": "int64",
    "MEDIUMINT": "int64",
    "REAL": "float64",
    "DOUBLE": "float64",
    "FLOAT": "float64",
    "DECIMAL": "decimal[12,2]",
    "NUMERIC": "decimal[12,2]",
    "BOOLEAN": "bool",
    "DATE": "date",
    "DATETIME": "datetime",
    "TIMESTAMP": "datetime",
    "TIME": "time",
    "CHAR": "string",
    "VARCHAR": "string",
    "TEXT": "string",
    "NCHAR": "string",
    "NVARCHAR": "string",
    "CLOB": "string",
    "BLOB": "bytes"
}



def format_prompt(prompt, data, question, database_content, script_content):
    if question in data:
        recomendation = data[question].get("context_id", "")
        similar_code = data[question].get("similar_queries", "similar code not found")
        question = data[question].get("redefined_question", question)
    else:
        recomendation = ""
        similar_code = "similar pydough_data code not found"
    
    return question, prompt.format(
        script_content=script_content,
        database_content=database_content,
        similar_queries=similar_code,
        recomendation=recomendation
    )

def convert_windows_to_wsl_path(windows_path: str) -> str:
    """Convert a Windows path to a WSL path."""
    # Remove drive letter and colon
    if ':' in windows_path:
        drive, path = windows_path.split(':', 1)
        # Convert to lowercase as WSL uses lowercase drive letters
        drive = drive.lower()
        # Replace backslashes with forward slashes
        path = path.replace('\\', '/')
        # Construct WSL path
        return f"/mnt/{drive}{path}"
    return windows_path

def generate_pydough_graph(db_path: str) -> Dict[str, Any]:
    """Generates a Pydough graph from the database schema."""
    # Convert Windows path to WSL path if running in WSL
    if os.name == 'posix' and ':' in db_path:
        db_path = convert_windows_to_wsl_path(db_path)
    
    print(f"Attempting to connect to database at: {db_path}")
    print(f"File exists: {os.path.exists(db_path)}")
    
    engine = create_engine(f"sqlite:///{db_path}")
    tables = {}
    
    try:
        with engine.connect() as conn:
            # Get table names
            table_names = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
            
            for table in table_names['name']:
                # Get column info
                columns = pd.read_sql(f"PRAGMA table_info({table});", conn)
                
                # Find primary key column(s)
                primary_keys = columns[columns['pk'] > 0]['name'].tolist()
                if not primary_keys:
                    # If no primary key is defined, use the first column as the key
                    primary_keys = [columns.iloc[0]['name']]
                
                # Create table properties
                properties = {}
                for _, row in columns.iterrows():
                    col_name = row['name'].lower()
                    col_type = row['type'].lower()
                    
                    # Map SQLite types to Pydough types
                    if 'int' in col_type:
                        pydough_type = 'int64'
                    elif 'char' in col_type or 'text' in col_type:
                        pydough_type = 'string'
                    elif 'decimal' in col_type or 'numeric' in col_type:
                        pydough_type = 'decimal[12,2]'
                    elif 'date' in col_type:
                        pydough_type = 'date'
                    else:
                        pydough_type = 'string'
                    
                    properties[col_name] = {
                        "type": "table_column",
                        "column_name": row['name'],
                        "data_type": pydough_type
                    }
                
                # Create table entry
                tables[table.lower()] = {
                    "type": "simple_table",
                    "table_path": f"main.{table}",
                    "unique_properties": [pk.lower() for pk in primary_keys],
                    "properties": properties
                }
        
        # Create the complete graph structure
        pydough_graph = {
            "TPCH": {
                "type": "graph",
                "version": "1.0",
                "tables": tables,
                "relationships": {}
            }
        }
        
        return pydough_graph
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        raise

def read_benchmark_questions(csv_path: str) -> pd.Series:
    """Read questions from benchmark CSV file."""
    try:
        df = pd.read_csv(csv_path)
        if "question" in df.columns:
            return df["question"]
        else:
            print("Error: 'question' column not found in CSV")
            return pd.Series(dtype=str)
    except Exception as e:
        print(f"Error reading benchmark CSV: {str(e)}")
        return pd.Series(dtype=str)
    

    
def process_benchmark(db_path: str, metadata_path: str, benchmark_path: str):
    """Process all questions from the benchmark CSV file."""
    # Convert paths to WSL format if needed
    if os.name == 'posix':
        db_path = convert_windows_to_wsl_path(db_path)
        metadata_path = convert_windows_to_wsl_path(metadata_path)
        benchmark_path = convert_windows_to_wsl_path(benchmark_path)
    
    print(f"\n=== Processing Benchmark ===")
    print(f"Database path: {db_path}")
    print(f"Metadata path: {metadata_path}")
    print(f"Benchmark path: {benchmark_path}")
    
    # Read questions from benchmark CSV
    print("\nReading benchmark CSV...")
    questions = read_benchmark_questions(benchmark_path)
    if questions.empty:
        print("No questions found in benchmark CSV")
        return
    
    # Take only the first question
    first_question = questions.iloc[0]
    print(f"\nFirst question: {first_question}")
    
    # Initialize the agent with metadata
    print("\nInitializing agent...")
    agent = PydoughGeneratorAgent(db_path, metadata_path)
    
    # Process the first question
    print("\nProcessing first question...")
    result = agent.generate_and_execute(first_question)
    
    print("\n=== Result ===")
    print(f"Question: {first_question}")
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Output: {result['dataframe']}")
        print(f"Code: {result['code']}")
    
    return [{'question': first_question, 'result': result}]

class PyDoughExecutionTool(BaseTool):
    """Tool for executing PyDough code and returning results."""
    
    name: str = "pydough_executor"
    description: str = """Executes PyDough code and returns the results as a pandas DataFrame.
    Input should be a Python code block containing PyDough operations.
    The code will be executed in a PyDough environment with access to the TPCH database."""
    
    db_path: str = Field(..., description="Path to the SQLite database file")
    metadata_path: str = Field(..., description="Path to the metadata graph JSON file")
    
    def __init__(self, db_path: str, metadata_path: str):
        """Initialize the PyDough execution tool with database paths."""
        super().__init__(db_path=db_path, metadata_path=metadata_path)
        
        # Initialize PyDough session
        self._setup_pydough_session()
    
    def _setup_pydough_session(self):
        """Set up the PyDough session with metadata and database connection."""
        # Convert paths to WSL format if needed
        if os.name == 'posix':
            db_path = convert_windows_to_wsl_path(self.db_path)
            metadata_path = convert_windows_to_wsl_path(self.metadata_path)
        else:
            db_path = self.db_path
            metadata_path = self.metadata_path
        
        # Load metadata and connect to database
        pydough.active_session.load_metadata_graph(metadata_path, "TPCH")
        pydough.active_session.connect_database("sqlite", database=db_path, check_same_thread=False)
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code from triple backticks in text."""
        print("\n=== Extracting Code ===")
        print("Complete model response:")
        print(response)
        
        if not isinstance(response, str):
            print("Error: Response is not a string")
            return ""
        
        # Extract code between triple backticks
        match = re.search(r"```python\n(.*?)\n```", response, re.DOTALL)
        if match:
            python_code = match.group(1).strip()
            print("\nExtracted code:")
            print(python_code)
            return python_code
        else:
            print("\nNo Python code block found in response")
            return ""
    
    def _execute_code(self, code: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Execute PyDough code and return the result."""
        try:
            # Create local environment
            local_env = {
                "pydough": pydough,
                "datetime": datetime
            }
            
            # Transform and execute the code
            transformed_source = transform_cell(code, "pydough.active_session.metadata", set(local_env))
            exec(transformed_source, {}, local_env)
            
            # Get the last variable assigned
            last_variable = list(local_env.values())[-1]
            print("\n=== Last Variable ===")
            print(last_variable)
            
            # Convert to DataFrame
            result_df = pydough.to_df(last_variable).to_json()#orient='records')
            return result_df, None
            
        except Exception as e:
            return None, str(e)
    
    def _run(self, code: str) -> Dict[str, Any]:
        """Execute the PyDough code and return the results."""
        # Extract code from the input
        extracted_code = self._extract_code(code)
        if not extracted_code:
            return {
                "error": "No valid Python code found in input. Please review code formatting rules and try again.",
                "dataframe": None,
                "code": code
            }
        
        # Execute the code
        result, error = self._execute_code(extracted_code)
        
        if error:
            return {
                "error": error,
                "dataframe": None,
                "code": extracted_code
            }
        
        # Convert DataFrame to JSON if result is a DataFrame
        if isinstance(result, pd.DataFrame):
            result_json = result.to_json(orient='records')
            return {
                "dataframe": result_json,
                "result": result,
                "code": extracted_code
            }
        
        return {
            "dataframe": result,
            "code": extracted_code
        }
    
    async def _arun(self, code: str) -> Dict[str, Any]:
        """Asynchronous version of _run."""
        return self._run(code)

class PydoughGeneratorAgent:
    def __init__(self, db_path: str, metadata_path: str = None, cheatsheet_path: str = None):
        """Initialize the PyDough generator agent.
        
        Args:
            db_path: Path to the SQLite database file
            metadata_path: Path to the metadata graph JSON file
            cheatsheet_path: Path to the cheatsheet markdown file
        """
        self.db_path = db_path
        self.metadata_path = metadata_path
        self.cheatsheet_path = cheatsheet_path
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0
        )
        
        # Create PyDough execution tool
        self.pydough_tool = PyDoughExecutionTool(
            db_path=self.db_path,
            metadata_path=self.metadata_path
        )
        
        # Create tools list
        self.tools = [self.pydough_tool]
        
        # Create the ReAct agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools
        )

    def _format_prompt(self, prompt: str) -> str:
        """Format the prompt with database schema information."""
        print("\n=== Formatting Prompt ===")
        
        try:
            # Read the database schema
            schema_path = os.path.join(os.path.dirname(__file__), "pydough_data", "database", "tcph_graph.md")
            with open(schema_path, 'r', encoding='utf-8') as f:
                database_content = f.read()
            
            # Read the PyDough cheatsheet
            cheatsheet_path = os.path.join(os.path.dirname(__file__), "pydough_data", "pydough_files", "cheatsheet_partition_overhaul.md")
            with open(cheatsheet_path, 'r', encoding='utf-8') as f:
                cheatsheet_content = f.read()
            
            # Read the prompt template
            template_path = os.path.join(os.path.dirname(__file__), "pydough_data", "prompts", "prompt_overhaul_baseline.md")
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Format the prompt using the template
            formatted_prompt = f"""<task_description>
You are an AI assistant tasked with converting natural language descriptions into PyDough code snippets. 
Your goal is to generate accurate and efficient PyDough code that can execute the requested database operations. 

General Guidelines as a Pydough Generator Agent:

1. You have access to tools for interacting with the database via Pydough. Only use the below tools. 
2. You MUST double check your query before executing it.
3. If you get an error while executing a query, rewrite the query and try again.

</task_description>

<context>
To assist you in this task, you will be provided with the following context:

1. **PyDough Reference File**  
This file contains the core concepts, functions, and syntax of the PyDough language. It serves as a reference for understanding the PyDough syntax and structure.

{cheatsheet_content}

2. **Database Structure Reference File**  
This file outlines the database schema, collections, fields, and relationships. It provides information about the underlying data structure and organization.

{database_content}

3. **Examples for Context**  
Here are some examples of PyDough code snippets along with their corresponding natural language questions. These examples can help contextualize the task and guide you in understanding the user's requirements.

4. **Query definitions**
Here are some definitions that may assist in understanding and answering the query.

[
    "Total Order Value is defined as the sum of extended_price * (1 - discount).",
    "Aggregate Revenue is defined as the sum of LineItem_ExtendedPrice minus the sum of LineItem_Discount.",
    "Average Revenue per Ship Date is defined as the sum of revenue divided by the count of distinct ship dates.",
    "Partial Revenue is defined as quantity * extended_price * (1 - discount).",
    "Profit is defined as revenue minus cost."
]
</context>

<instructions>
To generate the PyDough code snippet, follow these steps:

1. Carefully analyze the provided natural language description to identify the database query or manipulation required. Extract the main components, such as collections, fields, and operations.

2. Generate PyDough code that:
   - Uses clear and concise syntax, adhering to the correct functions, parameters, and structure outlined in the PyDough Reference File.
   - Avoids the bad examples referenced in the PyDough Reference File.
   - Properly references fields and tables as defined in the Database Structure Reference File.
   - Includes comments for any complex operations, where necessary.
   - Assigns the final query to a variable.
   - Ensures proper indentation.
   - Follows the rules for using contextless expressions properly.
   - Adheres to the syntax and structure outlined in the PyDough Reference File.
   - Compares values using the equality operator (==) when necessary.
   - Ensures variable names are different from the field names in the Database Structure Reference File.
   Here's the corrected version:
   - Ensure you start with the appropriate collection.
   - Returns only the exact data requested, without adding additional fields or information.
   - If you need to use the high-level top collection, use the appropriate name as defined in the Database Structure Reference File.
   - Refer to the provided definitions to answer the query when it requires a specific definition. For example, if the query asks for 'total order value,' use the definition provided.

3. Determine if PARTITION is necessary. If it is not required, explore alternative methods such as CALCULATE or aggregations to achieve the desired result. If PARTITION is truly needed, use it appropriately.

4. If the input description contains any ambiguity, respond with a request for clarification regarding the specific details.

5. Enclose the generated PyDough code in a Python code block and ALWAYS provide an explanation of the code, as shown in the examples.

</instructions>

<question>
{prompt}
</question>

Please provide your answer in the following format:
1. Analysis of the question
2. Step-by-step explanation of the solution
3. The PyDough code in a Python code block
4. Explanation of how the code works"""
            
            return formatted_prompt
            
        except Exception as e:
            print(f"Error formatting prompt: {str(e)}")
            raise

    def generate_and_execute(self, prompt: str) -> Dict[str, Any]:
        """Generate and execute PyDough code from a prompt."""
        print("\n=== Generating and Executing Code ===")
        try:
            # Format the prompt with database schema and system message
            print("Formatting prompt...")
            formatted_prompt = self._format_prompt(prompt)
            
            # Create messages for the model
            print("Creating messages for LLM...")
            messages = [
                SystemMessage(content="You are an expert at generating PyDough code to answer questions about databases."),
                HumanMessage(content=formatted_prompt)
            ]
            
            # Generate code using the LLM
            print("Generating code with LLM...")
            response = self.llm.invoke(messages)

            # Execute the code, and dataframe using the tool
            print("Executing code with PyDough tool...")
            result = self.pydough_tool._run(response.content)
            
            # Add the input prompt to the result
            result["input"] = prompt
            result["generator_response"] = response.content
            
            return result
            
        except Exception as e:
            print(f"\n=== Generation Error ===")
            print(f"Error in generate_and_execute: {str(e)}")
            return {
                "input": prompt,
                "dataframe": None,
                "error": str(e),
                "code": None
            }

if __name__ == "__main__":
    # TPCH database paths
    db_path = "C:/Users/david/bodo/TPCH/test_data/tpch.db"
    metadata_path = "C:/Users/david/bodo/TPCH/test_data/tpch_demo_graph.json"
    #benchmark_path = "C:/Users/david/bodo/TPCH/test_data/benchmark.csv"
    benchmark_path = "C:/Users/david/bodo/TPCH/test_data/questions.csv"
    # Process all questions from benchmark
    results = process_benchmark(db_path, metadata_path, benchmark_path)
    
    # Print summary of results
    if results:
        print("\n=== Benchmark Results Summary ===")
        for result in results:
            print(f"\nQuestion: {result['question']}")
            if 'error' in result['result']:
                print(f"Error: {result['result']['error']}")
            else:
                print(f"Output: {result['result']['dataframe']}") 