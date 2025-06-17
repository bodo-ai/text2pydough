from typing import List, Dict, Any, Union, Optional, Tuple
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool, BaseTool
from langchain_google_vertexai import ChatVertexAI
from langchain.memory import ConversationBufferMemory
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, END
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
from tools.pydough import PyDoughExecutionTool

from langchain.globals import set_verbose, set_debug

#set_verbose(True)   # high‑level chain/tool logs
# set_debug(True)   # uncomment for *very* low‑level I/O dumps

load_dotenv()


# Initialize models
TEMPERATURE = 0.7
TOP_P = 0.95
MODELS =["projects/316936339319/locations/us-central1/endpoints/4491730399348654080",
         "gemini-2.0-flash"]
#MODELS =["gemini-2.0-flash", "projects/316936339319/locations/us-central1/endpoints/4491730399348654080"]

def format_prompt(prompt, data, question, database_content, script_content):
    """Format the prompt with database schema information."""
    try:
        # Load the user template
        template_path = os.path.join(os.path.dirname(__file__), "pydough_data", "prompts", "user_template.md")
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        if question in data:
            recomendation = data[question].get("context_id", "")
            similar_code = data[question].get("similar_queries", "similar code not found")
            question = data[question].get("redefined_question", question)
        else:
            recomendation = ""
            similar_code = "similar pydough_data code not found"
        
        return question, template.format(
            script_content=script_content,
            database_content=database_content,
            similar_queries=similar_code,
            recomendation=recomendation,
            question=question
        )
    except Exception as e:
        print(f"Error formatting prompt: {str(e)}")
        raise

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
    
    # Set cheatsheet path using relative path
    cheatsheet_path = os.path.join(os.path.dirname(__file__), "pydough_data", "pydough_files", "cheatsheet_partition_overhaul.md")
    
    print(f"\n=== Processing Benchmark ===")
    print(f"Database path: {db_path}")
    print(f"Metadata path: {metadata_path}")
    print(f"Benchmark path: {benchmark_path}")
    print(f"Cheatsheet path: {cheatsheet_path}")
    
    # Read questions from benchmark CSV
    print("\nReading benchmark CSV...")
    questions = read_benchmark_questions(benchmark_path)
    if questions.empty:
        print("No questions found in benchmark CSV")
        return
    
    # Take only the first question
    first_question = questions.iloc[1]
    print(f"\nFirst question: {first_question}")
    
    # Initialize the agent with metadata and cheatsheet
    print("\nInitializing agent...")
    agent = PydoughGeneratorAgent(db_path, metadata_path, cheatsheet_path)
    
    # Process the first question
    print("\nProcessing first question...")
    result = agent.generate_and_execute(first_question)
    
    print("\n=== Result ===")
    print(f"Question: {first_question}")
    if 'error' in result:
        print(f"Error: {result['error']}")
        pass
    else:
        print(f"Output: {result['dataframe']}")
        print(f"Code: {result['pydough_code']}")
        pass
    
    return [{'question': first_question, 'result': result}]

class PydoughGeneratorAgent:
    def __init__(self, db_path: str, metadata_path: str = None, cheatsheet_path: str = None, model_name: str = None, temperature: float = TEMPERATURE, top_p: float = TOP_P):
        """Initialize the PyDough generator agent.
        
        Args:
            db_path: Path to the SQLite database file
            metadata_path: Path to the metadata graph JSON file
            cheatsheet_path: Path to the cheatsheet markdown file
            model_name: Name of the model to use. If None, uses the first model in MODELS list
            temperature: Temperature parameter for model generation (default: 1.0)
            top_p: Top-p parameter for model generation (default: 0.95)
        """
        self.db_path = db_path
        self.metadata_path = metadata_path
        self.cheatsheet_path = cheatsheet_path
        
        # Initialize LLM with selected model
        if model_name is None:
            model_name = MODELS[0]
            
        self.llm = ChatVertexAI(
            model=model_name,
            temperature=temperature,
            max_tokens=8192,
            max_retries=6,
            top_p=top_p,
            stop=None
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
            
            # Read the PyDough cheatsheet if provided
            cheatsheet_content = ""
            if self.cheatsheet_path:
                with open(self.cheatsheet_path, 'r', encoding='utf-8') as f:
                    cheatsheet_content = f.read()
            
            # Read the user template
            template_path = os.path.join(os.path.dirname(__file__), "pydough_data", "prompts", "user_template.md")
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # Format the prompt using the template
            formatted_prompt = template.format(
                script_content=cheatsheet_content,
                database_content=database_content,
                similar_queries="similar code not found",
                recomendation="",
                question=prompt
            )
            
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
            print(prompt)
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
            
            print("\nGEN AGENT:\n", response.content)

            # Execute the code, and dataframe using the tool
            print("Executing code with PyDough tool...")
            result = self.pydough_tool._run(response.content)
            
            # Add the input prompt to the result
            result["input"] = prompt
            result["generator_response"] = response.content
            
            print("\nGEN AGENT:\n", response.content)
            
            # If we have a code field from the tool, use it
            if "code" in result:
                result["pydough_code"] = result["code"]
            else:
                # Try to extract the code from the response
                import re
                code_match = re.search(r'```python\n(.*?)\n```', response.content, re.DOTALL)
                if code_match:
                    result["pydough_code"] = code_match.group(1).strip()
                else:
                    result["pydough_code"] = ""
            
            return result
            
        except Exception as e:
            print(f"\n=== Generation Error ===")
            print(f"Error in generate_and_execute: {str(e)}")
            return {
                "input": prompt,
                "dataframe": None,
                "pydough_code": "",
                "error": str(e)
            }

def build_pydough_graph(db_path: str, metadata_path: str):
    """Build a LangGraph for PyDough code generation and execution."""
    
    # 1. Tools ---------------------------------------------------------------
    pydough_tool = PyDoughExecutionTool(
        db_path=db_path,
        metadata_path=metadata_path
    )
    tools = [pydough_tool]

    # 2. LLM ---------------------------------------------------------------
    llm = ChatVertexAI(
        model=MODELS[0],
        temperature=TEMPERATURE,
        top_p = TOP_P,
        max_tokens=8192,
        max_retries=6,
        stop=None
    )

    # 3. Load system template -------------------------------------------
    system_template_path = os.path.join(os.path.dirname(__file__), "pydough_data", "prompts", "system_prompt.md")
    with open(system_template_path, 'r', encoding='utf-8') as f:
        SYSTEM_TEMPLATE = f.read()

    # 4. Create dynamic prompt function -------------------------------------------
    def get_prompt_messages(state):
        """Generate prompt messages based on current state."""
        try:
            # Read the database schema
            schema_path = os.path.join(os.path.dirname(__file__), "pydough_data", "database", "tcph_graph.md")
            with open(schema_path, 'r', encoding='utf-8') as f:
                database_content = f.read()
            
            # Read the PyDough cheatsheet
            cheatsheet_path = os.path.join(os.path.dirname(__file__), "pydough_data", "pydough_files", "cheatsheet_partition_overhaul.md")
            with open(cheatsheet_path, 'r', encoding='utf-8') as f:
                cheatsheet_content = f.read()
            
            # Format the system message with dynamic content
            sys_msg = SYSTEM_TEMPLATE.format(
                database_content=database_content,
                cheatsheet_content=cheatsheet_content,
                input=state["input"]
            )
            
            # Return messages list with system message, user input, and agent scratchpad
            return [
                SystemMessage(content=sys_msg),
                HumanMessage(content=state["input"]),
                MessagesPlaceholder("agent_scratchpad")
            ]
            
        except Exception as e:
            print(f"Error formatting prompt: {str(e)}")
            raise

    # 5. Create the ReAct agent ---------------------------------------------------
    agent_graph = create_react_agent(
        model=llm,
        tools=tools,
        prompt=get_prompt_messages
    )

    # 6. Post-processing node ---------------------------------------------
    sg = StateGraph(agent_graph)
    
    def tidy(state):
        """Pick out the last assistant message, the dataframe JSON, and the PyDough code."""
        final_msg = state["messages"][-1].content
        dataframe = state.get("pydough_executor", {}).get("dataframe")
        code = state.get("pydough_executor", {}).get("code")
        return {
            "answer": final_msg,
            "dataframe": dataframe,
            "code": code
        }

    sg.add_node("post", tidy)
    sg.add_edge(agent_graph.output, "post")
    sg.set_finish("post")
    
    return sg.compile()

if __name__ == "__main__":
    
    # Auto‑patch LangChain & LangGraph
    from openinference.instrumentation.langchain import LangChainInstrumentor 
    LangChainInstrumentor().instrument()

    # Register a Phoenix tracer
    from phoenix.otel import register
    tracer_provider = register(
        project_name=os.getenv("EXPERIMENT_NAME", "agent-team-debug"),  # Use environment variable with fallback
        auto_instrument=True          # captures every LC/LG call automatically
    )    
    # TPCH database paths
    db_path = "C:/Users/david/bodo/TPCH/test_data/tpch.db"
    metadata_path = "C:/Users/david/bodo/TPCH/test_data/tpch_demo_graph.json"
    benchmark_path = "C:/Users/david/bodo/TPCH/test_data/benchmark.csv"
    #benchmark_path = "C:/Users/david/bodo/TPCH/test_data/questions.csv"
    # Process all questions from benchmark
    results = process_benchmark(db_path, metadata_path, benchmark_path)
    
    # Print summary of results
    if results:
        print("\n=== Benchmark Results Summary ===")
        pass 