from typing import List, Dict, Any, Union, Optional, Tuple, TypedDict, Annotated
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool, BaseTool
from langchain_google_vertexai import ChatVertexAI
from langchain_google_vertexai.model_garden import ChatAnthropicVertex
from langchain_aws import ChatBedrockConverse
from langchain.memory import ConversationBufferMemory
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
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
import textwrap
from concurrent.futures import ThreadPoolExecutor
from pydough.unqualified import transform_cell
from pydantic import Field
from tools.pydough import PyDoughExecutionTool, BaselineExecutionTool
from tools.retriever import RetrieverTool
from pathlib import Path
import traceback
from contextlib import redirect_stdout, redirect_stderr
import io
import boto3

from langchain.globals import set_verbose, set_debug

#set_verbose(True)   # high‑level chain/tool logs
# set_debug(True)   # uncomment for *very* low‑level I/O dumps

load_dotenv()


# Initialize models
TEMPERATURE = 0.7
TOP_P = 0.95

# Available models by provider
GCP_MODELS = [
    "gemini-2.5-flash-preview-05-20",
    "gemini-2.0-flash",
    "projects/316936339319/locations/us-central1/endpoints/4491730399348654080"
]

AWS_MODELS = [
    "bedrock/us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    "bedrock/us.anthropic.claude-3-5-haiku-20241022-v1:0",
    "bedrock/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "bedrock/us.anthropic.claude-3-5-sonnet-20240620-v1:0"
]

AWS_MODELS = []

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

def create_llm(model_name: str, temperature: float = TEMPERATURE, top_p: float = TOP_P, top_k: int = 40):
    """Create an LLM instance based on the model name."""
    if model_name.startswith('codestral-'):
        # For Mistral AI models, use the correct format without @001 and specify publisher
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        # Remove @001 if present
        model_id = model_name.split('@')[0]
        return ChatVertexAI(
            publisher="mistralai",
            model_name=model_id,
            project=project,
            location=location,
            temperature=temperature,
            max_tokens=8192,
            max_retries=6,
            top_p=top_p,
            top_k=top_k,
            stop=None,
            model_kwargs={
                "tool_config": {
                    "function_calling_config": {
                        "mode": "AUTO",
                        "max_consecutive_function_calls": 1,
                    }
                }
            },
        )
    elif model_name.startswith('claude-'):
        # For Anthropic models, use ChatAnthropicVertex with us-east5
        location = "us-east5"  # Fixed region for Anthropic models
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        return ChatAnthropicVertex(
            model_name=model_name,  # just the ID (wrapper adds publisher)
            project=project,
            location=location,
            temperature=temperature,
            max_output_tokens=512,
            top_p=top_p,
            top_k=top_k
        )
    elif model_name in GCP_MODELS or 'projects/' in model_name or model_name.startswith('gemini-'):
        return ChatVertexAI(
            model=model_name,
            temperature=temperature,
            max_tokens=8192,
            max_retries=6,
            top_p=top_p,
            top_k=top_k,
            stop=None,
            model_kwargs={
                "tool_config": {
                    "function_calling_config": {
                        "mode": "AUTO",
                        "max_consecutive_function_calls": 1,
                    }
                }
            },
        )
    elif model_name in AWS_MODELS:
        bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
        return ChatBedrockConverse(
            model_id=model_name,
            client=bedrock_client,
            temperature=temperature,
            max_tokens=4096,
            top_p=top_p,
            top_k=top_k
        )
    else:
        raise ValueError(f"Unknown model: {model_name}")

# Match
# ```python\n<code>\n```
# or variations without explicit newlines after the language tag.
PY_RE = re.compile(r"```python[\s\n]*([\s\S]*?)```", re.DOTALL | re.IGNORECASE)
JSON_RE = re.compile(r"```json\s+(.*?)\s+```", re.DOTALL | re.IGNORECASE)

def load_context(include_schema: bool = True, include_cheatsheet: bool = True) -> str:
    """Load context from files."""
    context_parts = []
    
    # Get the *project* root (two levels up from this file)
    agents_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    project_root = agents_dir.parent  # ../generator_team
    base_dir = project_root  # alias used below
    
    if include_schema:
        schema_path = base_dir / "pydough_data" / "database" / "tcph_graph.md"
        if schema_path.exists():
            schema_md = schema_path.read_text()
        else:
            schema_md = ""  # avoid FileNotFoundError
        context_parts.append("### Database schema\n" + schema_md)

    if include_cheatsheet:
        cheatsheet_path = base_dir / "pydough_data" / "pydough_files" / "cheatsheet_partition_overhaul.md"
        if cheatsheet_path.exists():
            cheatsheet_md = cheatsheet_path.read_text()
        else:
            cheatsheet_md = ""
        context_parts.append("### PyDough cheatsheet\n" + cheatsheet_md)

    if not context_parts:
        return ""

    context = (
        "<context>\n\n"
        + "\n\n".join(context_parts) +
        "\n\n</context>\n\n"
        "Please ignore any THINK/ACT observations that precede this block."
    )
    return context

# Cache context in memory - will be updated based on agent configuration
CONTEXT_PREFIX = load_context()

def _get_ai_text(reply: dict | str) -> str:
    """
    Normalise the reply object (string | dict | graph state) to the raw
    assistant‑text we need to parse.
    """
    print("\n=== _get_ai_text Debug ===")
    print(f"Input type: {type(reply)}")
    print(f"Input content: {reply}")

    # Plain string → done
    if isinstance(reply, str):
        print("Returning string directly")
        return reply

    # Our compiled graph, tidy node, or tool may already return structured keys
    if isinstance(reply, dict) and {"answer", "code", "dataframe"} <= reply.keys():
        print("Found structured keys, returning answer")
        return reply["answer"]

    # LangGraph / AgentExecutor style: {"output": "..."}
    if isinstance(reply, dict) and "output" in reply:
        print("Found output key, returning output")
        return reply["output"]

    # New format: {"messages": [ HumanMessage(...), AIMessage(...), ... ]}
    if isinstance(reply, dict) and "messages" in reply and isinstance(reply["messages"], list):
        print("Found messages list, searching for last AI message")
        # iterate backwards to find the last assistant turn
        for msg in reversed(reply["messages"]):
            print(f"Checking message: {msg}")
            if isinstance(msg, AIMessage):               # LangChain class
                print("Found AIMessage, returning content")
                return msg.content
            # If you're using plain dicts instead of classes:
            if getattr(msg, "type", None) == "ai" or getattr(msg, "role", None) == "assistant":
                print("Found AI message in dict format, returning content")
                return msg["content"] if isinstance(msg, dict) else msg.content

    # Fallback: stringify whatever we got
    print("No matching format found, stringifying input")
    return str(reply)

def parse_reply(reply_obj: dict | str, db_path: str | None = None, metadata_path: str | None = None) -> dict[str, Any]:
    """
    Extract `answer` (raw assistant text), `code` (fenced ```python blocks),
    and `dataframe` (from fenced ```json blocks) from the heterogeneous
    objects LangGraph can return.

    We additionally accept *db_path* and *metadata_path* so that the follow-up
    execution of any generated PyDough snippet is carried out against **the
    same database and metadata graph** the agent was configured with.  This
    resolves issues where the fallback executor defaulted to the TPCH graph
    regardless of the actual dataset (e.g. Defog's *Broker* database).
    """
    print("\n=== parse_reply Debug ===")
    print(f"Input type: {type(reply_obj)}")
    print(f"Input content: {reply_obj}")

    txt = _get_ai_text(reply_obj)
    print(f"\nExtracted text: {txt}")

    # ------------------------------------------------------------------
    # Early-exit: If the assistant reply does **not** include a fenced
    # ```python ... ``` block we assume there is nothing to execute and
    # return the raw answer immediately.  This avoids attempting to run
    # arbitrary natural-language text through the PyDough executor and
    # therefore prevents confusing syntax errors such as the one reported
    # in issue #XYZ.
    # ------------------------------------------------------------------
    if PY_RE.search(txt) is None and not re.search(r"\bpydough\.", txt):
        # Still try to surface any dataframe that may have been embedded as
        # ```json ... ``` for convenience, but do not treat its absence as
        # an error.
        json_match = JSON_RE.search(txt)
        dataframe_json = None
        if json_match:
            try:
                dataframe_json = json_match.group(1).strip()
            except Exception:
                dataframe_json = None

        return {
            "answer": txt,
            "code": "",
            "dataframe": dataframe_json,
        }

    # Always attempt execution — whether we found a fenced block or not —
    # letting the BaselineExecutionTool decide if executable code is present.
    try:
        # Fall back to environment defaults only when explicit paths were not
        # supplied (preserves behaviour for external callers that may rely on
        # that assumption).
        exec_db_path = db_path or os.getenv("DB_PATH", "C:/Users/david/bodo/TPCH/test_data/tpch.db")
        exec_metadata_path = metadata_path or os.getenv("METADATA_PATH", "C:/Users/david/bodo/TPCH/test_data/tpch_demo_graph.json")

        pydough_tool = BaselineExecutionTool(
            db_path=exec_db_path,
            metadata_path=exec_metadata_path
        )

        execution_result = pydough_tool._run(txt)

        if "error" in execution_result:
            print("\n=== PyDough Execution Error ===")
            print(f"Error message: {execution_result['error']}")
            return {
                "answer": txt,
                "code": execution_result.get("code", ""),
                "dataframe": None,
                "error": execution_result["error"],
                "traceback": execution_result.get("traceback", "")
            }

        return {
            "answer": txt,
            "code": execution_result["code"],
            "dataframe": execution_result["dataframe"]
        }

    except Exception as e:
        print("\n=== PyDough Execution Exception ===")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        traceback.print_exc()
        return {
            "answer": txt,
            "code": "",
            "dataframe": None,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

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
    
    # Define retriever files
    retriever_files = [
        "cheatsheet_partition_overhaul.md",
        "prompt_overhaul_baseline.md"
    ]
    
    # Initialize the agent with metadata and cheatsheet
    print("\nInitializing agent...")
    agent = PydoughGeneratorAgent(
        db_path=db_path, 
        metadata_path=metadata_path, 
        cheatsheet_path=cheatsheet_path, 
        include_cheatsheet=False, 
        include_schema=True,
        retriever_files=retriever_files
    )
    
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
        print(f"Code: {result['code']}")
        pass
    
    return [{'question': first_question, 'result': result}]

class PydoughGeneratorAgent:
    def __init__(self, db_path: str, metadata_path: str = None, cheatsheet_path: str = None, 
                 system_prompt_path: str = None, model_name: str = None, 
                 temperature: float = TEMPERATURE, top_p: float = TOP_P, top_k: int = 40,
                 include_schema: bool = True, include_cheatsheet: bool = True,
                 retriever_files: List[str] = None, tools: List[BaseTool] = None,
                 recursion_limit: int = 20):
        """Initialize the PyDough generator agent.
        
        Args:
            db_path: Path to the SQLite database file
            metadata_path: Path to the metadata graph JSON file
            cheatsheet_path: Path to the cheatsheet markdown file
            system_prompt_path: Path to the system prompt template file
            model_name: Name of the model to use. If None, uses the first model in GCP_MODELS list
            temperature: Temperature parameter for model generation (default: 0.7)
            top_p: Top-p parameter for model generation (default: 0.95)
            top_k: Top-k parameter for model generation (default: 40)
            include_schema: Whether to include database schema in context (default: True)
            include_cheatsheet: Whether to include PyDough cheatsheet in context (default: True)
            retriever_files: List of files to include in the retriever tool (default: None)
            tools: List of tools to use (default: None)
            recursion_limit: Maximum number of reasoning / tool-use steps before the graph aborts (default: 20)
        """
        # Handle database path for both Windows and WSL environments
        if os.path.exists("/mnt/c"):
            # WSL environment
            if not db_path.startswith("/mnt/"):
                db_path = convert_windows_to_wsl_path(db_path)
        else:
            # Windows environment
            if db_path.startswith("/mnt/"):
                db_path = db_path.replace("/mnt/c", "C:").replace("/", "\\")

        # Verify database exists
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found at {db_path}")

        self.db_path = db_path
        self.metadata_path = metadata_path
        self.cheatsheet_path = cheatsheet_path
        self.include_schema = include_schema
        self.include_cheatsheet = include_cheatsheet
        # Maximum number of reasoning / tool-use steps before the graph aborts
        self.recursion_limit = recursion_limit
        
        # Initialize LLM with selected model
        if model_name is None:
            model_name = GCP_MODELS[0]
            
        self.llm = create_llm(model_name, temperature, top_p, top_k)
        
        # Store the tools list
        self.tools = tools or []
        
        # Load system prompt template
        if system_prompt_path is None:
            system_prompt_path = os.path.join(os.path.dirname(__file__), "pydough_data", "prompts", "system_prompt.md")
        
        with open(system_prompt_path, 'r', encoding='utf-8') as f:
            raw_prompt = f.read()

        # Replace template placeholders (e.g. {dialect}, {top_k}) if they exist so that
        # ChatPromptTemplate does not later raise `INVALID_PROMPT_INPUT` when those
        # variables are not supplied at runtime.  Default to SQLite as the dialect
        # and the `top_k` value already provided to the constructor.
        try:
            if ("{dialect}" in raw_prompt) or ("{top_k}" in raw_prompt):
                self.system_prompt = raw_prompt.format(dialect="SQLite", top_k=top_k)
            else:
                self.system_prompt = raw_prompt
        except KeyError:
            # In case the prompt has additional placeholders we haven't provided,
            # fall back to the raw prompt to avoid crashing and let the template
            # engine surface the explicit error for debugging.
            self.system_prompt = raw_prompt
        
        # Build the ChatPromptTemplate and pre-fill any remaining template variables.
        self.prompt = (
            ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                MessagesPlaceholder("messages"),
                # MessagesPlaceholder("agent_scratchpad")  # ReAct thoughts (optional)
            ])
            .partial(dialect="SQLite", top_k=str(top_k))
        )
        
        # Create ReAct agent if tools are provided
        if self.tools:
            self.agent = create_react_agent(
                model=self.llm,
                tools=self.tools,  # Pass all tools directly since they now have _run
                prompt=self.prompt
            )

    def generate_and_execute(self, question: str) -> Dict[str, Any]:
        """Generate and execute PyDough code from a question."""
        try:
            # Generate context based on agent configuration
            context = load_context(
                include_schema=self.include_schema,
                include_cheatsheet=self.include_cheatsheet
            )
            
            # Prepend context to the question if there is any
            user_msg = f"{context}\n\n<question>\n{question}\n</question>" if context else f"<question>\n{question}\n</question>"
            
            if not self.tools:
                # Direct LLM generation without tools
                messages = [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=user_msg)
                ]
                response = self.llm.invoke(messages)
                return {
                    "input": question,
                    "answer": response.content,
                    "code": "",
                    "dataframe": None
                }
            else:
                # Use ReAct agent with tools
                # Pass the message content directly as a string
                reply = self.agent.invoke({
                    "messages": [HumanMessage(content=user_msg)],
                }, config={"recursion_limit": self.recursion_limit})
                content = reply
                print("\nV2\n")
                print(content)
                # Parse and return result
                result = parse_reply(content, self.db_path, self.metadata_path)
                result["input"] = question
                return result
            
        except Exception as e:
            print(f"\n=== Generation Error ===")
            print(f"Error in generate_and_execute: {str(e)}")
            return {
                "input": question,
                "dataframe": None,
                "code": "",
                "error": str(e)
            }

class AgentState(TypedDict):
    """State for the agent workflow."""
    messages: List[Union[HumanMessage, AIMessage, SystemMessage]]
    pydough_executor: Dict[str, Any]

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
        model=GCP_MODELS[0],
        temperature=TEMPERATURE,
        top_p=TOP_P,
        max_tokens=8192,
        max_retries=6,
        stop=None,
        model_kwargs={
            "tool_config": {
                "function_calling_config": {
                    "mode": "AUTO",
                    "max_consecutive_function_calls": 1,
                }
            }
        },
    )

    # 3. Load system template and content -------------------------------------------
    system_template_path = os.path.join(os.path.dirname(__file__), "pydough_data", "prompts", "system_prompt.md")
    with open(system_template_path, 'r', encoding='utf-8') as f:
        SYSTEM_MSG = f.read()
    
    # Create the prompt template
    PROMPT_TMPL = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_MSG),
        MessagesPlaceholder("messages"),
        MessagesPlaceholder("agent_scratchpad"),
        MessagesPlaceholder("code")
    ])

    # 4. Create the ReAct agent ---------------------------------------------------
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=PROMPT_TMPL
    )

    # 5. Create and configure the graph ---------------------------------------------
    workflow = StateGraph(AgentState)
    
    # Add the agent node
    workflow.add_node("agent", agent)
    
    # Add post-processing node
    def tidy(state: AgentState) -> Dict[str, Any]:
        """Pick out the last assistant message, the dataframe JSON, and the PyDough code."""
        final_msg = state.get("messages", [])[-1].content if state.get("messages") else ""
        dataframe = state.get("pydough_executor", {}).get("dataframe")
        code = state.get("pydough_executor", {}).get("code")
        return {
            "answer": final_msg,
            "dataframe": dataframe,
            "code": code
        }
    
    workflow.add_node("post", tidy)
    
    # Set up the edges
    workflow.add_edge("agent", "post")
    
    # Set entry and finish points
    workflow.set_entry_point("agent")
    workflow.set_finish_point("post")
    
    return workflow.compile()

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
    system_prompt_path = os.path.join(os.path.dirname(__file__), "pydough_data", "prompts", "system_prompt.md")
    
    # Process all questions from benchmark
    agent = PydoughGeneratorAgent(
        db_path=db_path,
        metadata_path=metadata_path,
        system_prompt_path=system_prompt_path,
        include_cheatsheet=True,
        include_schema=True
    )
    
    results = process_benchmark(db_path, metadata_path, benchmark_path)
    
    # Print summary of results
    if results:
        print("\n=== Benchmark Results Summary ===")
        pass 