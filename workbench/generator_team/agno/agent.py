import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.google import Gemini
from typing import List, Dict, Any, Union, Optional, Tuple
import pandas as pd
from pydough import active_session
from pydough.unqualified import transform_cell
from sqlalchemy import create_engine
import json
import argparse

from agno.tools.python import PythonTools
from pydough_toolkit import PyDoughExecutionToolkit

# Load environment variables from .env file
load_dotenv()

def convert_windows_to_wsl_path(windows_path: str) -> str:
    """Convert a Windows path to a WSL path."""
    if ':' in windows_path:
        drive, path = windows_path.split(':', 1)
        drive = drive.lower()
        path = path.replace('\\', '/')
        return f"/mnt/{drive}{path}"
    return windows_path

# Set base paths in WSL format
BASE_DIR = "/mnt/c/Users/david/bodo"
TPCH_DIR = f"{BASE_DIR}/TPCH"
TEST_DATA_DIR = f"{TPCH_DIR}/test_data"

# Initialize paths
db_path = convert_windows_to_wsl_path(os.path.join(TEST_DATA_DIR, "tpch.db"))
metadata_path = convert_windows_to_wsl_path(os.path.join(TEST_DATA_DIR, "tpch_demo_graph.json"))
benchmark_path = convert_windows_to_wsl_path(os.path.join(TEST_DATA_DIR, "benchmark.csv"))

MODELS =["gemini-2.0-flash",
         "projects/316936339319/locations/us-central1/endpoints/4491730399348654080"]

# Initialize Gemini model with environment variables
gemini_vertex = Gemini(
    id= MODELS[1],
    vertexai=True,
    project_id=os.getenv("GCP_PROJECT"),
    location=os.getenv("GCP_PROJECT_LOCATION", "us-central1"),
    temperature=0.3,
    max_output_tokens=8192,
)

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
    
    # Verify files exist
    for path, name in [(db_path, "Database"), (metadata_path, "Metadata"), (benchmark_path, "Benchmark")]:
        if not os.path.exists(path):
            print(f"Error: {name} file not found at {path}")
            return
    
    # Read questions from benchmark CSV
    print("\nReading benchmark CSV...")
    questions = read_benchmark_questions(benchmark_path)
    if questions.empty:
        print("No questions found in benchmark CSV")
        return
    
    # Take only the first question
    first_question = questions.iloc[0]
    print(f"\nFirst question: {first_question}")
    
    # Read the database schema from metadata file
    print("\nReading database schema...")
    with open(metadata_path, 'r', encoding='utf-8') as f:
        database_content = f.read()
    
    # Initialize the agent with metadata
    print("\nInitializing agent...")
    agent = Agent(
        model=gemini_vertex,
        tools=[
            PyDoughExecutionToolkit(db_url=db_path),
        ],
        markdown=True,
        debug_mode=True, 
        show_tool_calls=True,
    )
    
    # Create prompt with database schema
    prompt = f"""<task_description>
You are an AI assistant tasked with converting natural language descriptions into PyDough code snippets. 
Your goal is to generate accurate and efficient PyDough code that can execute the requested database operations. 

General Guidelines as a Pydough Generator Agent:

1. You have access to tools for interacting with the database via Pydough. Only use the below tools. 
2. You MUST double check your query before executing it.
3. If you get an error while executing a query, rewrite the query and try again.

</task_description>

<context>
To assist you in this task, you will be provided with the following context:

1. **Database Structure Reference File**  
This file outlines the database schema, collections, fields, and relationships. It provides information about the underlying data structure and organization.

{database_content}

2. **Query definitions**
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
   - Uses clear and concise syntax, adhering to the correct functions, parameters, and structure.
   - Properly references fields and tables as defined in the Database Structure Reference File.
   - Includes comments for any complex operations, where necessary.
   - Assigns the final query to a variable.
   - Ensures proper indentation.
   - Follows the rules for using contextless expressions properly.
   - Compares values using the equality operator (==) when necessary.
   - Ensures variable names are different from the field names in the Database Structure Reference File.
   - Starts with the appropriate collection.

3. Execute the code using the tool:
```json
{{"tool": "pydough_tools.run_pydough_query",
 "args": {{"expression": "YOUR_PYDOUGH_EXPRESSION"}}}}
```

Question: {first_question}

Please provide your answer in the following format:
1. Analysis of the question
2. Step-by-step explanation of the solution
3. The PyDough code in a Python code block
4. Tool execution result"""
    
    # Process the first question
    print("\nProcessing first question...")
    response = agent.run(prompt)
    
    print("\n=== Result ===")
    print(f"Question: {first_question}")
    print(f"Response: {response.content}")
    
    return [{'question': first_question, 'response': response.content}]

# Load metadata and connect to database
active_session.load_metadata_graph(metadata_path, "TPCH")
active_session.connect_database("sqlite", database=db_path, check_same_thread=False)

if __name__ == "__main__":
    # Process the benchmark
    results = process_benchmark(db_path, metadata_path, benchmark_path) 