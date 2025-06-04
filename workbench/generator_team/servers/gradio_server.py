import gradio as gr
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
import uuid
from typing import Dict, Any, List, Tuple
import logging
from datetime import datetime
from dotenv import load_dotenv
import os
import sys

# Add parent directory to Python path to find tools module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
# Ensure workspace root (grandparent) is on path so that `import generator_team` works when uvicorn reloads
grandparent_dir = os.path.dirname(parent_dir)
if grandparent_dir not in sys.path:
    sys.path.insert(0, grandparent_dir)

import vertexai
from vertexai.preview.generative_models import GenerativeModel
from google.cloud import aiplatform_v1 as aiplatform
from langchain_google_vertexai.model_garden import ChatAnthropicVertex
import mlflow
from mlflow.tracking import MlflowClient
import pandas as pd
from tools.pydough import PyDoughExecutionTool, BaselineExecutionTool
from tools.retriever import RetrieverTool
from langchain.tools import BaseTool
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from generator_team.agents.ReAct import create_llm, PydoughGeneratorAgent
from generator_team.agents.SelfHealingReact import SelfHealingSQLAgent  # NEW
from generator_team.agents.multiagent_supervisor import create_supervisor_app  # NEW

# Global path configurations

CLOUD_RUN=False

if CLOUD_RUN:

    WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Move up one more level
    PYDOUGH_DATA_DIR = os.path.join(WORKSPACE_ROOT, "generator_team", "pydough_data")
    PROMPTS_DIR = os.path.join(PYDOUGH_DATA_DIR, "prompts")
    PYDOUGH_FILES_DIR = os.path.join(PYDOUGH_DATA_DIR, "pydough_files")
    DEFAULT_DB_PATH = os.path.join(WORKSPACE_ROOT, "mount-folder","datasets","TPCH", "TPC-H.db")
    DEFAULT_METADATA_PATH = os.path.join(WORKSPACE_ROOT, "mount-folder","datasets","TPCH", "tpch_demo_graph.json")
    DEFAULT_PROMPT_FILE = "system_prompt.md"
    DEFAULT_RETRIEVER_FILE = "cheatsheet_partition_overhaul.md"
    
else:

    WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Move up one more level
    PYDOUGH_DATA_DIR = os.path.join(WORKSPACE_ROOT, "generator_team", "pydough_data")
    PROMPTS_DIR = os.path.join(PYDOUGH_DATA_DIR, "prompts")
    PYDOUGH_FILES_DIR = os.path.join(PYDOUGH_DATA_DIR, "pydough_files")
    DEFAULT_DB_PATH = os.path.join(WORKSPACE_ROOT, "TPCH", "test_data", "tpch.db")
    DEFAULT_METADATA_PATH = os.path.join(WORKSPACE_ROOT, "TPCH", "test_data", "tpch_demo_graph.json")
    DEFAULT_PROMPT_FILE = "system_prompt.md"
    DEFAULT_RETRIEVER_FILE = "cheatsheet_partition_overhaul.md"

load_dotenv()

# Global variable to control logging backend
USE_MLFLOW = False  # Set to False to use Phoenix instead

# Configure MLflow
if USE_MLFLOW:
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    MLFLOW_TRACKING_TOKEN = os.getenv("MLFLOW_TRACKING_TOKEN", "")
    # print(MLFLOW_TRACKING_URI)
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(os.getenv("EXPERIMENT_NAME", "agent-playground"))
    # Enable MLflow LangChain autologging
    mlflow.langchain.autolog(
        log_traces=True,
        log_models=True,
        log_input_examples=True,
        log_model_signatures=True,
        registered_model_name="pydough_agent"
    )
else:
    # Register a Phoenix tracer
    from phoenix.otel import register
    API_KEY = os.getenv("PHOENIX_API_KEY")
    COLLECTOR_ENDPOINT = os.getenv("PHOENIX_COLLECTOR_ENDPOINT")  # Ej: "http://mlflow-alb-1071096006.us-east-2.elb.amazonaws.com:6060/v1/traces"

    tracer_provider = register(
        endpoint=COLLECTOR_ENDPOINT,               # URL raíz sin /v1/traces
        headers={"Authorization": f"Bearer {API_KEY}"},
        project_name=os.getenv("EXPERIMENT_NAME", "agent-react-sql"),
        auto_instrument=True,
        protocol="http/protobuf"                    # Forzar uso HTTP en lugar de gRPC
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

# Now import the agent module
from generator_team.agents.ReAct import (
    PydoughGeneratorAgent, 
    AgentState, 
    GCP_MODELS, 
    AWS_MODELS, 
    load_context
)

# Import Anthropic model configuration
from servers.gcp_model_call import MODEL_ID as ANTHROPIC_MODEL_ID

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Set root logger to WARNING
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Set this specific logger to WARNING
# Set all loggers to WARNING level
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).setLevel(logging.WARNING)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="PyDough Generator Agent API with Gradio UI")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Available Gemini models (fallback)
GEMINI_MODELS = [
    "gemini-2.5-flash-preview-04-17",
    "gemini-2.5-flash-preview-05-20",
    "gemini-2.5-pro-preview-05-06",
    "gemini-2.0-flash", 
]

# Available Mistral models
MISTRAL_MODELS = [
    "codestral-2501"
]

# Anthropic model
ANTHROPIC_MODELS = [
    ANTHROPIC_MODEL_ID,
    "claude-opus-4@20250514",
    "claude-sonnet-4@20250514"
]

# Cache for available models
_available_models_cache = None

def get_available_models() -> List[dict]:
    """Fetch available endpoints from GCP and add AWS models."""
    global _available_models_cache
    
    # Return cached models if available
    if _available_models_cache is not None:
        return _available_models_cache
        
    try:
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        available_models = []
        
        # Add AWS models first
        for model in AWS_MODELS:
            available_models.append({
                "name": model,
                "display": f"AWS: {model}",
                "provider": "AWS"
            })
        
        # Add default GCP models
        for model in GCP_MODELS:
            available_models.append({
                "name": model,
                "display": f"GCP: {model}",
                "provider": "GCP"
            })
            
        # Add Gemini models
        for model in GEMINI_MODELS:
            available_models.append({
                "name": model,
                "display": f"Gemini: {model}",
                "provider": "Gemini"
            })

        # Add Mistral models
        for model in MISTRAL_MODELS:
            available_models.append({
                "name": model,
                "display": f"Mistral: {model}",
                "provider": "Mistral"
            })

        # Add Anthropic models
        for model in ANTHROPIC_MODELS:
            available_models.append({
                "name": model,
                "display": f"Anthropic: {model}",
                "provider": "Anthropic"
            })
        
        if not project:
            logger.warning("GCP project not set in environment variables")
            _available_models_cache = available_models
            return _available_models_cache
            
        # Initialize Vertex AI
        vertexai.init(project=project, location=location)
        
        # Initialize the Endpoint client
        client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        client = aiplatform.EndpointServiceClient(client_options=client_options)
        
        parent = f"projects/{project}/locations/{location}"
        logger.info(f"Listing endpoints from parent: {parent}")
        
        # Add discovered GCP endpoints
        for ep in client.list_endpoints(parent=parent):
            # Extract a shorter version of the endpoint name for display
            endpoint_id = ep.name.split('/')[-1]
            model_info = {
                "name": ep.name,
                "display": f"GCP: {ep.display_name} (ID: {endpoint_id})",
                "provider": "GCP"
            }
            logger.info(f"Found endpoint: {model_info['display']}")
            available_models.append(model_info)
        
        logger.info(f"Found {len(available_models)} total models")
        _available_models_cache = available_models
        return _available_models_cache
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}", exc_info=True)
        # Return at least the default models if there's an error
        _available_models_cache = available_models
        return _available_models_cache

def get_available_databases() -> List[Dict[str, str]]:
    """Get list of available databases with their categories."""
    try:
        databases = []
        
        # Get TPCH databases
        default_db_dir = os.path.dirname(DEFAULT_DB_PATH)
        logger.info(f"Looking for TPCH databases in: {default_db_dir}")
        if os.path.exists(default_db_dir):
            tpch_dbs = [f for f in os.listdir(default_db_dir) if f.endswith('.db')]
            logger.info(f"Found TPCH databases: {tpch_dbs}")
            for db in tpch_dbs:
                databases.append({
                    "name": db,
                    "display": f"TPCH: {db}",
                    "category": "TPCH"
                })
        
        # Get KaggleDBQA databases
        # First try the Windows path
        kaggle_db_dir = os.path.join(WORKSPACE_ROOT, "KaggleDBQA", "databases")
        # Convert to WSL path
        wsl_kaggle_db_dir = convert_windows_to_wsl_path(kaggle_db_dir)
        logger.info(f"Looking for KaggleDBQA databases in: {wsl_kaggle_db_dir}")
        
        if os.path.exists(wsl_kaggle_db_dir):
            # First level directories (e.g., dev_databases, GeoNuclearData, etc.)
            for top_dir in os.listdir(wsl_kaggle_db_dir):
                top_dir_path = os.path.join(wsl_kaggle_db_dir, top_dir)
                if os.path.isdir(top_dir_path):
                    logger.info(f"Checking top-level directory: {top_dir}")
                    
                    # Check for databases in the top-level directory
                    db_files = [f for f in os.listdir(top_dir_path) if f.endswith(('.db', '.sqlite'))]
                    if db_files:
                        logger.info(f"Found database files in {top_dir}: {db_files}")
                        for db_file in db_files:
                            databases.append({
                                "name": f"{top_dir}/{db_file}",
                                "display": f"KaggleDBQA: {top_dir}/{db_file}",
                                "category": "KaggleDBQA"
                            })
                    
                    # Check for nested directories (e.g., dev_databases/...)
                    for sub_dir in os.listdir(top_dir_path):
                        sub_dir_path = os.path.join(top_dir_path, sub_dir)
                        if os.path.isdir(sub_dir_path):
                            logger.info(f"Checking subdirectory: {top_dir}/{sub_dir}")
                            sub_db_files = [f for f in os.listdir(sub_dir_path) if f.endswith(('.db', '.sqlite'))]
                            if sub_db_files:
                                logger.info(f"Found database files in {top_dir}/{sub_dir}: {sub_db_files}")
                                for db_file in sub_db_files:
                                    databases.append({
                                        "name": f"{top_dir}/{sub_dir}/{db_file}",
                                        "display": f"KaggleDBQA: {top_dir}/{sub_dir}/{db_file}",
                                        "category": "KaggleDBQA"
                                    })
        else:
            logger.error(f"KaggleDBQA directory not found: {wsl_kaggle_db_dir}")
            logger.error(f"Windows path: {kaggle_db_dir}")
            logger.error(f"WORKSPACE_ROOT: {WORKSPACE_ROOT}")
        
        # Get Spider databases
        spider_db_dir = os.path.join(WORKSPACE_ROOT, "spider_data", "databases")
        wsl_spider_db_dir = convert_windows_to_wsl_path(spider_db_dir)
        logger.info(f"Looking for Spider databases in: {wsl_spider_db_dir}")
        
        if os.path.exists(wsl_spider_db_dir):
            for dataset_dir in os.listdir(wsl_spider_db_dir):
                dataset_path = os.path.join(wsl_spider_db_dir, dataset_dir)
                if os.path.isdir(dataset_path):
                    # Databases directly under dataset directory
                    db_files = [f for f in os.listdir(dataset_path) if f.endswith((".db", ".sqlite"))]
                    if db_files:
                        logger.info(f"Found database files in {dataset_dir}: {db_files}")
                        for db_file in db_files:
                            databases.append({
                                "name": f"{dataset_dir}/{db_file}",
                                "display": f"Spider: {dataset_dir}/{db_file}",
                                "category": "Spider"
                            })
                    # Check for nested directories inside dataset directory (rare)
                    for sub_dir in os.listdir(dataset_path):
                        sub_dir_path = os.path.join(dataset_path, sub_dir)
                        if os.path.isdir(sub_dir_path):
                            sub_db_files = [f for f in os.listdir(sub_dir_path) if f.endswith((".db", ".sqlite"))]
                            if sub_db_files:
                                logger.info(f"Found database files in {dataset_dir}/{sub_dir}: {sub_db_files}")
                                for db_file in sub_db_files:
                                    databases.append({
                                        "name": f"{dataset_dir}/{sub_dir}/{db_file}",
                                        "display": f"Spider: {dataset_dir}/{sub_dir}/{db_file}",
                                        "category": "Spider"
                                    })
        else:
            logger.error(f"Spider directory not found: {wsl_spider_db_dir}")
        
        # BEGIN Defog dataset support ------------------------------------------------
        defog_db_dir = os.path.join(WORKSPACE_ROOT, "Defog", "databases")
        wsl_defog_db_dir = convert_windows_to_wsl_path(defog_db_dir)
        logger.info(f"Looking for Defog databases in: {wsl_defog_db_dir}")
        
        if os.path.exists(wsl_defog_db_dir):
            # Databases directly under Defog/databases
            root_db_files = [f for f in os.listdir(wsl_defog_db_dir) if f.endswith((".db", ".sqlite"))]
            if root_db_files:
                logger.info(f"Found root-level Defog databases: {root_db_files}")
                for db_file in root_db_files:
                    databases.append({
                        "name": db_file,
                        "display": f"Defog: {db_file}",
                        "category": "Defog"
                    })
            # Iterate over first-level directories (e.g., Broker, Ewallet, ...)
            for top_dir in os.listdir(wsl_defog_db_dir):
                top_dir_path = os.path.join(wsl_defog_db_dir, top_dir)
                if os.path.isdir(top_dir_path):
                    logger.info(f"Checking Defog directory: {top_dir}")
                    # Databases directly inside top_dir
                    db_files = [f for f in os.listdir(top_dir_path) if f.endswith((".db", ".sqlite"))]
                    if db_files:
                        logger.info(f"Found database files in {top_dir}: {db_files}")
                        for db_file in db_files:
                            databases.append({
                                "name": f"{top_dir}/{db_file}",
                                "display": f"Defog: {top_dir}/{db_file}",
                                "category": "Defog"
                            })
                    # Nested subdirectories under top_dir
                    for sub_dir in os.listdir(top_dir_path):
                        sub_dir_path = os.path.join(top_dir_path, sub_dir)
                        if os.path.isdir(sub_dir_path):
                            sub_db_files = [f for f in os.listdir(sub_dir_path) if f.endswith((".db", ".sqlite"))]
                            if sub_db_files:
                                logger.info(f"Found database files in {top_dir}/{sub_dir}: {sub_db_files}")
                                for db_file in sub_db_files:
                                    databases.append({
                                        "name": f"{top_dir}/{sub_dir}/{db_file}",
                                        "display": f"Defog: {top_dir}/{sub_dir}/{db_file}",
                                        "category": "Defog"
                                    })
        else:
            logger.error(f"Defog directory not found: {wsl_defog_db_dir}")
        # END Defog dataset support --------------------------------------------------
        
        # Remove root-level Defog databases to avoid duplicates
        databases = [d for d in databases if not (d.get("category") == "Defog" and '/' not in d.get("name", ""))]
        
        # Log all found databases
        logger.info(f"Total available databases: {databases}")
        
        if not databases:
            logger.warning("No databases found in any location")
            return []
            
        return databases
    except Exception as e:
        logger.error(f"Error getting available databases: {str(e)}", exc_info=True)
        logger.error(f"WORKSPACE_ROOT: {WORKSPACE_ROOT}")
        logger.error(f"Current working directory: {os.getcwd()}")
        return []

def get_available_retriever_files() -> List[str]:
    """Get list of available retriever files."""
    try:
        # Convert to WSL path if needed
        wsl_retriever_dir = convert_windows_to_wsl_path(PYDOUGH_FILES_DIR)
        
        # List all .md files in the directory
        if os.path.exists(wsl_retriever_dir):
            retriever_files = [f for f in os.listdir(wsl_retriever_dir) if f.endswith('.md')]
            if not retriever_files:
                logger.warning(f"No .md files found in {wsl_retriever_dir}")
                return [DEFAULT_RETRIEVER_FILE]  # Fallback to default
            return retriever_files
        else:
            logger.error(f"Retriever directory not found: {wsl_retriever_dir}")
            return [DEFAULT_RETRIEVER_FILE]  # Fallback to default
    except Exception as e:
        logger.error(f"Error getting available retriever files: {str(e)}")
        return [DEFAULT_RETRIEVER_FILE]  # Fallback to default

def get_available_prompt_files() -> List[str]:
    """Get list of available prompt template files."""
    try:
        # Convert to WSL path if needed
        wsl_prompt_dir = convert_windows_to_wsl_path(PROMPTS_DIR)
        
        # List all .md files in the directory
        if os.path.exists(wsl_prompt_dir):
            prompt_files = [f for f in os.listdir(wsl_prompt_dir) if f.endswith('.md')]
            if not prompt_files:
                logger.warning(f"No .md files found in {wsl_prompt_dir}")
                return [DEFAULT_PROMPT_FILE]  # Fallback to default
            return prompt_files
        else:
            logger.error(f"Prompt directory not found: {wsl_prompt_dir}")
            return [DEFAULT_PROMPT_FILE]  # Fallback to default
    except Exception as e:
        logger.error(f"Error getting available prompt files: {str(e)}")
        return [DEFAULT_PROMPT_FILE]  # Fallback to default

def load_prompt_template(prompt_file: str) -> str:
    """Load the contents of a prompt template file."""
    try:
        prompt_path = os.path.join(PROMPTS_DIR, prompt_file)
        wsl_prompt_path = convert_windows_to_wsl_path(prompt_path)
        
        if os.path.exists(wsl_prompt_path):
            with open(wsl_prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            logger.error(f"Prompt file not found: {wsl_prompt_path}")
            return ""
    except Exception as e:
        logger.error(f"Error loading prompt template: {str(e)}")
        return ""

def save_prompt_template(prompt_file: str, content: str) -> bool:
    """Save the contents to a prompt template file."""
    try:
        prompt_path = os.path.join(PROMPTS_DIR, prompt_file)
        wsl_prompt_path = convert_windows_to_wsl_path(prompt_path)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(wsl_prompt_path), exist_ok=True)
        
        with open(wsl_prompt_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Error saving prompt template: {str(e)}")
        return False

# Initialize the agent
db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
metadata_path = os.getenv("METADATA_PATH", DEFAULT_METADATA_PATH)

def create_agent(model_name: str, retriever_file: str, prompt_file: str, temperature: float = 0.7, top_p: float = 0.95, top_k: int = 40, pydough_tool: bool = True, sql_list_tables: bool = True, sql_schema: bool = True, sql_query: bool = False, sql_query_checker: bool = False, document_kb: bool = True, db_path: str = None, metadata_path: str = None, recursion_limit: int = 20) -> PydoughGeneratorAgent:
    """Create a new agent instance with the specified model or endpoint."""
    # If db_path is not supplied, fall back to default logic
    if db_path is None:
        base_db_path = os.getenv("DB_PATH", DEFAULT_DB_PATH)
    else:
        base_db_path = db_path
    # Determine metadata path if not provided
    if metadata_path is None:
        base_metadata_path = os.getenv("METADATA_PATH", DEFAULT_METADATA_PATH)
    else:
        base_metadata_path = metadata_path
    
    # Check if the model_name is an endpoint (contains 'projects/')
    if 'projects/' in model_name:
        endpoint_name = model_name
    elif model_name.startswith('codestral-'):
        endpoint_name = model_name.split('@')[0]
    elif model_name.startswith(('claude-', 'anthropic.')):
        endpoint_name = model_name
    else:
        endpoint_name = model_name
    
    # Convert to WSL paths
    wsl_db_path = convert_windows_to_wsl_path(base_db_path)
    wsl_metadata_path = convert_windows_to_wsl_path(base_metadata_path)
    
    # Get the full path for the retriever file
    retriever_path = os.path.join(PYDOUGH_FILES_DIR, retriever_file)
    wsl_retriever_path = convert_windows_to_wsl_path(retriever_path)
    
    # Get the full path for the prompt file
    prompt_path = os.path.join(PROMPTS_DIR, prompt_file)
    wsl_prompt_path = convert_windows_to_wsl_path(prompt_path)
    
    # Initialize tools list
    tools = []
    
    # Determine graph name for metadata
    graph_name = "TPCH"
    # If metadata_path filename follows pattern <graph_name>_graph.json, extract it
    try:
        base_name = os.path.basename(base_metadata_path or "")
        if base_name.endswith("_graph.json"):
            graph_name = base_name.replace("_graph.json", "")
    except Exception:
        pass

    if pydough_tool:
        pydough_tool_instance = PyDoughExecutionTool(db_path=wsl_db_path, metadata_path=wsl_metadata_path, graph_name=graph_name)
        tools.append(pydough_tool_instance)
    
    if any([sql_list_tables, sql_schema, sql_query, sql_query_checker]):
        db_uri = f"sqlite:///{wsl_db_path}"
        db = SQLDatabase.from_uri(db_uri)
        sql_toolkit = SQLDatabaseToolkit(db=db, llm=create_llm(endpoint_name, temperature, top_p, top_k))
        sql_tools = sql_toolkit.get_tools()
        enabled_sql_tools = []
        for tool in sql_tools:
            if tool.name == 'sql_db_list_tables' and sql_list_tables:
                enabled_sql_tools.append(tool)
            elif tool.name == 'sql_db_schema' and sql_schema:
                enabled_sql_tools.append(tool)
            elif tool.name == 'sql_db_query' and sql_query:
                enabled_sql_tools.append(tool)
            elif tool.name == 'sql_db_query_checker' and sql_query_checker:
                enabled_sql_tools.append(tool)
        tools.extend(enabled_sql_tools)
    
    if document_kb and retriever_file:
        abs_retriever_files = []
        if not os.path.isabs(wsl_retriever_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            wsl_retriever_path = os.path.join(base_dir, "pydough_data", "pydough_files", retriever_file)
        abs_retriever_files.append(wsl_retriever_path)
        retriever = RetrieverTool(input_files=abs_retriever_files, collection_name="pydough_docs", model_name="text-embedding-005")
        tools.append(retriever.get_tool(name="document_kb", description="Semantic search over Pydough documentation and examples."))
    
    return PydoughGeneratorAgent(model_name=endpoint_name, db_path=wsl_db_path, metadata_path=wsl_metadata_path, include_cheatsheet=False, include_schema=False, retriever_files=[wsl_retriever_path] if document_kb else None, system_prompt_path=wsl_prompt_path, temperature=temperature, top_p=top_p, top_k=top_k, tools=tools, recursion_limit=recursion_limit)

# Store threads in memory
threads_store: Dict[str, Dict[str, Any]] = {}

def create_thread():
    """Create a new thread."""
    thread_id = str(uuid.uuid4())
    threads_store[thread_id] = {"created_at": datetime.utcnow()}
    return thread_id

def process_message(message: str, history: List[Tuple[str, str]], architecture_dropdown: str, model_display: str, include_cheatsheet: bool, include_schema: bool, retriever_file: str, prompt_file: str, temperature: float, top_p: float, top_k: int, max_steps: int, pydough_tool: bool, sql_list_tables: bool, sql_schema: bool, sql_query: bool, sql_query_checker: bool, document_kb: bool, selected_db_display: str, use_sh_query_gen: bool = False) -> List[Tuple[str, str]]:
    """Process a message and return the response."""
    try:
        # Find the model name from the display name
        models = get_available_models()
        model_info = next((m for m in models if m["display"] == model_display), None)
        if not model_info:
            raise ValueError(f"Model not found: {model_display}")
            
        # Find the database info from the display name
        available_dbs = get_available_databases()
        db_info = next((db for db in available_dbs if db["display"] == selected_db_display), None)
        if not db_info:
            raise ValueError(f"Database not found: {selected_db_display}")
            
        # Get the database path based on selection
        selected_db = db_info["name"]
        if db_info["category"] == "KaggleDBQA":
            # Split the path into components
            path_parts = selected_db.split('/')
            if len(path_parts) == 2:  # top_dir/db_file
                db_folder, db_file = path_parts
                db_path = os.path.join(WORKSPACE_ROOT, "KaggleDBQA", "databases", db_folder, db_file)
                metadata_path = os.path.join(WORKSPACE_ROOT, "KaggleDBQA", "metadata", f"{db_folder}_graph.json")
            elif len(path_parts) == 3:  # top_dir/sub_dir/db_file
                top_dir, sub_dir, db_file = path_parts
                db_path = os.path.join(WORKSPACE_ROOT, "KaggleDBQA", "databases", top_dir, sub_dir, db_file)
                metadata_path = os.path.join(WORKSPACE_ROOT, "KaggleDBQA", "metadata", f"{top_dir}_{sub_dir}_graph.json")
            else:
                raise ValueError(f"Invalid database path format: {selected_db}")
        elif db_info["category"] == "Spider":
            # Split the path into components similar to KaggleDBQA
            path_parts = selected_db.split('/')
            if len(path_parts) == 2:  # dataset/db_file
                dataset, db_file = path_parts
                db_path = os.path.join(WORKSPACE_ROOT, "spider_data", "databases", dataset, db_file)
                metadata_path = os.path.join(WORKSPACE_ROOT, "spider_data", "metadata", f"{dataset}_graph.json")
            elif len(path_parts) == 3:  # dataset/sub_dir/db_file (rare)
                dataset, sub_dir, db_file = path_parts
                db_path = os.path.join(WORKSPACE_ROOT, "spider_data", "databases", dataset, sub_dir, db_file)
                metadata_path = os.path.join(WORKSPACE_ROOT, "spider_data", "metadata", f"{dataset}_{sub_dir}_graph.json")
            else:
                raise ValueError(f"Invalid database path format: {selected_db}")
        elif db_info["category"] == "Defog":
            # Handle Defog dataset paths
            path_parts = selected_db.split('/')
            if len(path_parts) == 2:  # top_dir/db_file
                db_folder, db_file = path_parts
                db_path = os.path.join(WORKSPACE_ROOT, "Defog", "databases", db_folder, db_file)
                metadata_path = os.path.join(WORKSPACE_ROOT, "Defog", "metadata", f"{db_folder}_graph.json")
            elif len(path_parts) == 3:  # top_dir/sub_dir/db_file
                top_dir, sub_dir, db_file = path_parts
                db_path = os.path.join(WORKSPACE_ROOT, "Defog", "databases", top_dir, sub_dir, db_file)
                metadata_path = os.path.join(WORKSPACE_ROOT, "Defog", "metadata", f"{top_dir}_{sub_dir}_graph.json")
            elif len(path_parts) == 1:  # db_file directly under databases/
                db_file = path_parts[0]
                db_path = os.path.join(WORKSPACE_ROOT, "Defog", "databases", db_file)
                base_name = os.path.splitext(db_file)[0]
                metadata_path = os.path.join(WORKSPACE_ROOT, "Defog", "metadata", f"{base_name}_graph.json")
            else:
                raise ValueError(f"Invalid database path format: {selected_db}")
        else:  # TPCH database
            db_path = os.path.join(os.path.dirname(DEFAULT_DB_PATH), selected_db)
            metadata_path = DEFAULT_METADATA_PATH
        
        # Convert Windows paths to WSL paths for the database and metadata
        wsl_db_path = convert_windows_to_wsl_path(db_path)
        wsl_metadata_path = convert_windows_to_wsl_path(metadata_path)
        
        # ARCHITECTURE SELECTION -------------------------------------------------
        use_self_healing = architecture_dropdown.startswith("Self-Healing")
        is_multiagent = architecture_dropdown.startswith("Multi-Agent")

        if is_multiagent:
            # Build and invoke the Supervisor → Workers LangGraph application
            try:
                from langchain_core.messages import HumanMessage

                supervisor_app = create_supervisor_app(
                    model=model_info["name"],
                    db_path=wsl_db_path,
                    metadata_path=wsl_metadata_path,
                    pydough_agent_kwargs={
                        "include_cheatsheet": include_cheatsheet,
                        "include_schema": include_schema,
                    },
                    use_selfhealing_query_generator=use_sh_query_gen,
                )

                state = supervisor_app.invoke({"messages": [HumanMessage(content=message)]})
                msgs = state.get("messages", []) if isinstance(state, dict) else []
                # Concatenate contents from **assistant/AI** messages to preserve full answer
                answer_parts = []
                for _m in msgs:
                    role = getattr(_m, "role", None) or getattr(_m, "type", None)
                    if role in ("assistant", "ai") or _m.__class__.__name__ == "AIMessage":
                        if hasattr(_m, "content") and _m.content is not None:
                            answer_parts.append(_m.content if isinstance(_m.content, str) else str(_m.content))
                answer = "\n\n".join(answer_parts) if answer_parts else (msgs[-1].content if msgs else "")
                # Replace the last placeholder assistant message
                new_history = history.copy()
                if new_history and new_history[-1][1] is None:
                    # Overwrite the assistant "None" placeholder
                    user_msg = new_history[-1][0]
                    new_history[-1] = (user_msg, answer)
                else:
                    # Fallback – append if placeholder pattern not found
                    new_history.append((message, answer))
                return new_history
            except Exception as e:
                logger.error(f"Error in multi-agent process: {str(e)}")
                new_history = history.copy()
                if new_history and new_history[-1][1] is None:
                    user_msg = new_history[-1][0]
                    new_history[-1] = (user_msg, f"Error: {str(e)}")
                else:
                    new_history.append((message, f"Error: {str(e)}"))
                return new_history

        # Existing Self-Healing route
        if use_self_healing:
            # Instantiate the Self-Healing SQL agent (simpler pipeline)
            sh_agent = SelfHealingSQLAgent(
                db_path=wsl_db_path,
                model_name=model_info["name"],
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                max_steps=max_steps,
            )  # NEW
            state = sh_agent.ask(message)  # NEW
            msgs = state.get("messages", []) if isinstance(state, dict) else []  # NEW
            answer_parts = []
            for _m in msgs:
                role = getattr(_m, "role", None) or getattr(_m, "type", None)
                if role in ("assistant", "ai") or _m.__class__.__name__ == "AIMessage":
                    if hasattr(_m, "content") and _m.content is not None:
                        answer_parts.append(_m.content if isinstance(_m.content, str) else str(_m.content))
            answer = "\n\n".join(answer_parts) if answer_parts else (msgs[-1].content if msgs else "")  # NEW
            new_history = history.copy()
            if new_history and new_history[-1][1] is None:
                user_msg = new_history[-1][0]
                new_history[-1] = (user_msg, answer)
            else:
                new_history.append((message, answer))
            return new_history  # NEW
        # -----------------------------------------------------------------------
        # Existing ReAct (PyDough) workflow
        agent = create_agent(
            model_info["name"], 
            retriever_file, 
            prompt_file, 
            temperature, 
            top_p, 
            top_k,
            pydough_tool,
            sql_list_tables,
            sql_schema,
            sql_query,
            sql_query_checker,
            document_kb,
            wsl_db_path,
            wsl_metadata_path,
            recursion_limit=max_steps
        )
        
        # Update agent configuration
        agent.include_cheatsheet = include_cheatsheet
        agent.include_schema = include_schema
        
        if USE_MLFLOW:
            # Invoking the chain will cause a trace to be logged
            with mlflow.start_run():
                # Generate and execute the response
                result = agent.generate_and_execute(message)
        else:
            # Generate and execute the response
            result = agent.generate_and_execute(message)
        
        # Format the response
        response = result.get("answer", "")
        if result.get("error"):
            response += f"\n\nError: {result['error']}"
            if result.get("traceback"):
                response += f"\n\nTraceback:\n{result['traceback']}"
        
        # Add the new message pair to history
        new_history = history.copy()
        if new_history and new_history[-1][1] is None:
            user_msg = new_history[-1][0]
            new_history[-1] = (user_msg, response)
        else:
            new_history.append((message, response))
        return new_history
    except Exception as e:
        logger.error(f"Error in process_message: {str(e)}")
        error_message = f"Error: {str(e)}"
        new_history = history.copy()
        if new_history and new_history[-1][1] is None:
            user_msg = new_history[-1][0]
            new_history[-1] = (user_msg, error_message)
        else:
            new_history.append((message, error_message))
        return new_history

# Create Gradio interface
with gr.Blocks(title="PyDough Generator Agent") as demo:
    gr.Markdown("# PyDough Generator Agent Playground")
    gr.Markdown("Ask questions about your data and get PyDough code generated and executed.")
    
    # Get the model list once
    available_models = get_available_models()
    
    # Get available databases
    available_dbs = get_available_databases()
    logger.info(f"Initializing database dropdown with: {available_dbs}")
    
    with gr.Row():
        model_dropdown = gr.Dropdown(
            choices=[m["display"] for m in available_models],
            value=available_models[0]["display"],
            label="Select Model"
        )
        # (Architecture accordion moved below System Prompt Template)
        # Update database dropdown to use the full list of databases with categories
        db_dropdown = gr.Dropdown(
            choices=[db["display"] for db in available_dbs],
            value=available_dbs[0]["display"] if available_dbs else None,
            label="Select Database",
            #info="Select a database to query. TPCH databases are in the root, KaggleDBQA databases are in their respective folders.",
            interactive=True,
            allow_custom_value=False
        )
        retriever_dropdown = gr.Dropdown(
            choices=get_available_retriever_files(),
            value=DEFAULT_RETRIEVER_FILE,
            label="Select Retriever File"
        )
        prompt_dropdown = gr.Dropdown(
            choices=get_available_prompt_files(),
            value=DEFAULT_PROMPT_FILE,
            label="Select System Prompt Template"
        )
    
    # Add prompt template editor in an accordion
    with gr.Accordion("System Prompt Template", open=False):
        with gr.Row():
            prompt_editor = gr.Textbox(
                label="System Prompt Template",
                lines=10,
                interactive=True,
                value=load_prompt_template("system_prompt.md")
            )
        with gr.Row():
            save_prompt_btn = gr.Button("Save Prompt Template")
    
    # Add the Architecture selector accordion just below the System Prompt Template
    with gr.Accordion("Architecture", open=False):  # Moved here
        architecture_dropdown = gr.Radio(
            choices=[
                "ReAct (PyDough)",
                "Self-Healing SQL",
                "Multi-Agent Supervisor",
            ],
            value="ReAct (PyDough)",
            label="Agent Architecture",
        )
        max_steps_slider = gr.Slider(
            minimum=1,
            maximum=20,
            value=10,
            step=1,
            label="Recursion Limit (Max Steps)",
            interactive=True,
        )
        # Checkbox specific to the Multi-Agent Supervisor architecture
        use_sh_query_gen_chk = gr.Checkbox(
            value=False,
            label="Use Self-Healing Query Generator",
            visible=False,
            info="Replace the default query_generator worker with Self-Healing SQL Agent when enabled.",
        )
    
    with gr.Row():
        include_cheatsheet = gr.Checkbox(
            value=False,
            label="Include Cheatsheet in Context"
        )
        include_schema = gr.Checkbox(
            value=False,
            label="Include Schema in Context"
        )
    
    # Dynamically show / hide the Supervisor-specific controls based on the selection
    def _toggle_supervisor_controls(selected_arch):
        is_sup = selected_arch == "Multi-Agent Supervisor"
        return gr.update(visible=is_sup)

    architecture_dropdown.change(
        _toggle_supervisor_controls,
        inputs=[architecture_dropdown],
        outputs=[use_sh_query_gen_chk],
    )
    
    # Replace the tools section with an Accordion
    with gr.Accordion("Available Tools", open=False):
        with gr.Row():
            pydough_tool = gr.Checkbox(
                value=True,
                label="PyDough Execution Tool",
                info="Executes PyDough code and returns results as a DataFrame"
            )
            sql_list_tables = gr.Checkbox(
                value=True,
                label="SQL List Tables",
                info="List all tables in the database"
            )
            sql_schema = gr.Checkbox(
                value=True,
                label="SQL Schema",
                info="Get the schema of specific tables"
            )
        with gr.Row():
            sql_query = gr.Checkbox(
                value=False,
                label="SQL Query",
                info="Execute SQL queries directly"
            )
            sql_query_checker = gr.Checkbox(
                value=False,
                label="SQL Query Checker",
                info="Validate SQL queries before execution"
            )
            document_kb = gr.Checkbox(
                value=True,
                label="Document Knowledge Base",
                info="Semantic search over PyDough documentation"
            )
    
    with gr.Row():
        temperature = gr.Slider(
            minimum=0.0,
            maximum=1.0,
            value=0.7,
            step=0.1,
            label="Temperature"
        )
        top_p = gr.Slider(
            minimum=0.0,
            maximum=1.0,
            value=0.95,
            step=0.05,
            label="Top P"
        )
        top_k = gr.Slider(
            minimum=1,
            maximum=100,
            value=40,
            step=1,
            label="Top K"
        )
    
    # Chat interface
    chatbot = gr.Chatbot(
        height=600,
        type="tuples"  # Use tuples format for message pairs
    )
    msg = gr.Textbox(placeholder="Ask a question about your data...", label="Question")
    clear = gr.Button("Clear")
    
    # Add a separator
    gr.Markdown("---")
    
    # SQL execution section
    with gr.Accordion("SQL Execution", open=False):
        gr.Markdown("## SQL Query Execution")
        with gr.Row():
            sql_query = gr.Textbox(
                label="Enter SQL Query",
                placeholder="SELECT * FROM table_name LIMIT 10",
                lines=5
            )
            preview_rows = gr.Slider(
                minimum=1,
                maximum=100,
                value=10,
                step=1,
                label="Rows to Display"
            )
        
        with gr.Row():
            execute_btn = gr.Button("Execute Query")
            clear_sql_btn = gr.Button("Clear Query")
        
        sql_preview = gr.Dataframe(
            label="Query Results",
            interactive=False,
            wrap=True
        )
        
        def execute_sql_query(query: str, num_rows: int, selected_db_display: str):
            if not query:
                return None
            try:
                # Find the database info from the display name
                available_dbs = get_available_databases()
                db_info = next((db for db in available_dbs if db["display"] == selected_db_display), None)
                if not db_info:
                    raise ValueError(f"Database not found: {selected_db_display}")
                
                # Get the database path based on selection
                selected_db = db_info["name"]
                if db_info["category"] == "KaggleDBQA":
                    # Split the path into components
                    path_parts = selected_db.split('/')
                    if len(path_parts) == 2:  # top_dir/db_file
                        db_folder, db_file = path_parts
                        db_path = os.path.join(WORKSPACE_ROOT, "KaggleDBQA", "databases", db_folder, db_file)
                    elif len(path_parts) == 3:  # top_dir/sub_dir/db_file
                        top_dir, sub_dir, db_file = path_parts
                        db_path = os.path.join(WORKSPACE_ROOT, "KaggleDBQA", "databases", top_dir, sub_dir, db_file)
                    else:
                        raise ValueError(f"Invalid database path format: {selected_db}")
                elif db_info["category"] == "Spider":
                    # Split the path into components similar to KaggleDBQA
                    path_parts = selected_db.split('/')
                    if len(path_parts) == 2:  # dataset/db_file
                        dataset, db_file = path_parts
                        db_path = os.path.join(WORKSPACE_ROOT, "spider_data", "databases", dataset, db_file)
                    elif len(path_parts) == 3:  # dataset/sub_dir/db_file (rare)
                        dataset, sub_dir, db_file = path_parts
                        db_path = os.path.join(WORKSPACE_ROOT, "spider_data", "databases", dataset, sub_dir, db_file)
                    else:
                        raise ValueError(f"Invalid database path format: {selected_db}")
                elif db_info["category"] == "Defog":
                    path_parts = selected_db.split('/')
                    if len(path_parts) == 2:  # top_dir/db_file
                        db_folder, db_file = path_parts
                        db_path = os.path.join(WORKSPACE_ROOT, "Defog", "databases", db_folder, db_file)
                    elif len(path_parts) == 3:  # top_dir/sub_dir/db_file
                        top_dir, sub_dir, db_file = path_parts
                        db_path = os.path.join(WORKSPACE_ROOT, "Defog", "databases", top_dir, sub_dir, db_file)
                    elif len(path_parts) == 1:  # db_file directly under databases/
                        db_file = path_parts[0]
                        db_path = os.path.join(WORKSPACE_ROOT, "Defog", "databases", db_file)
                    else:
                        raise ValueError(f"Invalid database path format: {selected_db}")
                else:  # TPCH database
                    db_path = os.path.join(os.path.dirname(DEFAULT_DB_PATH), selected_db)
                
                # Convert Windows path to WSL path for the database
                wsl_db_path = convert_windows_to_wsl_path(db_path)
                db_uri = f"sqlite:///{wsl_db_path}"
                db = SQLDatabase.from_uri(db_uri)
                
                # Execute query and get results as DataFrame
                engine = getattr(db, "engine", None) or db._engine
                df = pd.read_sql_query(query, engine)
                
                # Return first n rows
                return df.head(num_rows)
            except Exception as e:
                logger.error(f"Error executing SQL query: {str(e)}")
                return None
        
        execute_btn.click(
            execute_sql_query,
            inputs=[sql_query, preview_rows, db_dropdown],
            outputs=[sql_preview]
        )
        
        clear_sql_btn.click(
            lambda: ("", None),
            inputs=[],
            outputs=[sql_query, sql_preview]
        )
    
    # PyDough execution section
    with gr.Accordion("PyDough Execution", open=False):
        gr.Markdown("## PyDough Code Execution")
        with gr.Row():
            pydough_code = gr.Textbox(
                label="Enter PyDough Code",
                placeholder="Example:\npydough.scan('customer').limit(10)",
                lines=10
            )
            pyd_preview_rows = gr.Slider(
                minimum=1,
                maximum=100,
                value=10,
                step=1,
                label="Rows to Display"
            )
        
        with gr.Row():
            execute_pydough_btn = gr.Button("Execute PyDough")
            clear_pydough_btn = gr.Button("Clear")
        
        pydough_preview = gr.Dataframe(
            label="PyDough Results",
            interactive=False,
            wrap=True
        )
        
        def execute_pydough_code(code: str, num_rows: int, selected_db_display: str):
            if not code:
                return None
            try:
                # Find database info based on selection
                available_dbs = get_available_databases()
                db_info = next((db for db in available_dbs if db["display"] == selected_db_display), None)
                if not db_info:
                    raise ValueError(f"Database not found: {selected_db_display}")
                
                # Determine database and metadata paths (mirrors SQL logic)
                selected_db = db_info["name"]
                if db_info["category"] == "KaggleDBQA":
                    path_parts = selected_db.split('/')
                    if len(path_parts) == 2:  # top_dir/db_file
                        db_folder, db_file = path_parts
                        db_path = os.path.join(WORKSPACE_ROOT, "KaggleDBQA", "databases", db_folder, db_file)
                        metadata_path = os.path.join(WORKSPACE_ROOT, "KaggleDBQA", "metadata", f"{db_folder}_graph.json")
                    elif len(path_parts) == 3:  # top_dir/sub_dir/db_file
                        top_dir, sub_dir, db_file = path_parts
                        db_path = os.path.join(WORKSPACE_ROOT, "KaggleDBQA", "databases", top_dir, sub_dir, db_file)
                        metadata_path = os.path.join(WORKSPACE_ROOT, "KaggleDBQA", "metadata", f"{top_dir}_{sub_dir}_graph.json")
                    else:
                        raise ValueError(f"Invalid database path format: {selected_db}")
                elif db_info["category"] == "Spider":
                    path_parts = selected_db.split('/')
                    if len(path_parts) == 2:
                        dataset, db_file = path_parts
                        db_path = os.path.join(WORKSPACE_ROOT, "spider_data", "databases", dataset, db_file)
                        metadata_path = os.path.join(WORKSPACE_ROOT, "spider_data", "metadata", f"{dataset}_graph.json")
                    elif len(path_parts) == 3:
                        dataset, sub_dir, db_file = path_parts
                        db_path = os.path.join(WORKSPACE_ROOT, "spider_data", "databases", dataset, sub_dir, db_file)
                        metadata_path = os.path.join(WORKSPACE_ROOT, "spider_data", "metadata", f"{dataset}_{sub_dir}_graph.json")
                    else:
                        raise ValueError(f"Invalid database path format: {selected_db}")
                elif db_info["category"] == "Defog":
                    path_parts = selected_db.split('/')
                    if len(path_parts) == 2:
                        db_folder, db_file = path_parts
                        db_path = os.path.join(WORKSPACE_ROOT, "Defog", "databases", db_folder, db_file)
                        metadata_path = os.path.join(WORKSPACE_ROOT, "Defog", "metadata", f"{db_folder}_graph.json")
                    elif len(path_parts) == 3:
                        top_dir, sub_dir, db_file = path_parts
                        db_path = os.path.join(WORKSPACE_ROOT, "Defog", "databases", top_dir, sub_dir, db_file)
                        metadata_path = os.path.join(WORKSPACE_ROOT, "Defog", "metadata", f"{top_dir}_{sub_dir}_graph.json")
                    elif len(path_parts) == 1:
                        db_file = path_parts[0]
                        db_path = os.path.join(WORKSPACE_ROOT, "Defog", "databases", db_file)
                        base_name = os.path.splitext(db_file)[0]
                        metadata_path = os.path.join(WORKSPACE_ROOT, "Defog", "metadata", f"{base_name}_graph.json")
                    else:
                        raise ValueError(f"Invalid database path format: {selected_db}")
                else:  # TPCH
                    db_path = os.path.join(os.path.dirname(DEFAULT_DB_PATH), selected_db)
                    metadata_path = DEFAULT_METADATA_PATH
                
                # Convert to WSL paths where applicable
                wsl_db_path = convert_windows_to_wsl_path(db_path)
                wsl_metadata_path = convert_windows_to_wsl_path(metadata_path)
                
                # Determine graph name from metadata file name
                graph_name = "TPCH"
                base_name = os.path.basename(metadata_path)
                if base_name.endswith("_graph.json"):
                    graph_name = base_name.replace("_graph.json", "")
                
                # Execute PyDough code via BaselineExecutionTool
                tool = BaselineExecutionTool(db_path=wsl_db_path, metadata_path=wsl_metadata_path, graph_name=graph_name)
                result = tool._run(code)
                
                if result.get("error"):
                    raise ValueError(result["error"])
                
                data_json = result.get("dataframe")
                if data_json is None:
                    return None
                
                df = pd.read_json(data_json, orient='records')
                return df.head(num_rows)
            except Exception as e:
                logger.error(f"Error executing PyDough code: {str(e)}")
                return None
        
        execute_pydough_btn.click(
            execute_pydough_code,
            inputs=[pydough_code, pyd_preview_rows, db_dropdown],
            outputs=[pydough_preview]
        )
        
        clear_pydough_btn.click(
            lambda: ("", None),
            inputs=[],
            outputs=[pydough_code, pydough_preview]
        )
    
    # CSV file upload and preview section moved below chat
    with gr.Accordion("CSV Data Preview", open=False):
        gr.Markdown("## CSV Data Preview")
        with gr.Row():
            csv_file = gr.File(
                label="Select CSV File",
                file_types=[".csv"],
                type="filepath"
            )
            preview_rows = gr.Slider(
                minimum=1,
                maximum=100,
                value=20,
                step=1,
                label="Rows per Page"
            )
        
        # Add column selector
        column_selector = gr.Dropdown(
            label="Select Columns to Display",
            choices=[],
            value=[],
            multiselect=True,
            interactive=True,
            allow_custom_value=True,
            info="Select columns to display. You can remove and add back columns at any time."
        )
        
        # Add filter input box
        filter_input = gr.Textbox(
            label="Filter Data",
            placeholder="Enter filter conditions (e.g., 'column_name > 100' or 'column_name.str.contains(\"text\")')",
            info="Use pandas query syntax to filter data. Examples: 'age > 30', 'name.str.contains(\"John\")', 'salary >= 50000'",
            lines=2
        )
        
        # Add copy buttons
        with gr.Row():
            copy_selected_btn = gr.Button("Copy Selected Cells")
            copy_all_btn = gr.Button("Copy All Data")
            copy_columns_btn = gr.Button("Copy Selected Columns")
        
        csv_preview = gr.Dataframe(
            label="CSV Preview",
            interactive=True,
            wrap=True,
            column_widths=["auto"] * 100,
            datatype=["str"] * 100,
            type="pandas",
            row_count=(20, "dynamic"),
            col_count=(100, "dynamic")
        )
        
        load_more_btn = gr.Button("Load More Rows")
        
        # Store the current position in the CSV file
        current_position = gr.State(0)
        
        # Add copy functionality
        def copy_selected_cells(df):
            if df is None:
                return "No data to copy"
            try:
                # Get selected cells from the dataframe
                selected_data = df.iloc[df.index.get_level_values(0), df.columns.get_level_values(0)]
                # Convert to string representation
                return selected_data.to_string()
            except Exception as e:
                return f"Error copying data: {str(e)}"
        
        def copy_all_data(df):
            if df is None:
                return "No data to copy"
            try:
                # Convert entire dataframe to string representation
                return df.to_string()
            except Exception as e:
                return f"Error copying data: {str(e)}"
        
        def copy_selected_columns(df, columns):
            if df is None or not columns:
                return "No data to copy"
            try:
                # Get selected columns
                selected_data = df[columns]
                # Convert to string representation
                return selected_data.to_string()
            except Exception as e:
                return f"Error copying data: {str(e)}"
        
        # Add copy button handlers
        copy_selected_btn.click(
            copy_selected_cells,
            inputs=[csv_preview],
            outputs=[gr.Textbox(label="Copied Data", interactive=False)]
        )
        
        copy_all_btn.click(
            copy_all_data,
            inputs=[csv_preview],
            outputs=[gr.Textbox(label="Copied Data", interactive=False)]
        )
        
        copy_columns_btn.click(
            copy_selected_columns,
            inputs=[csv_preview, column_selector],
            outputs=[gr.Textbox(label="Copied Data", interactive=False)]
        )
    
    def get_available_csv_files() -> List[str]:
        """Get list of available CSV files in the local environment directory."""
        try:
            # Use the same directory as the database files
            csv_dir = os.path.dirname(DEFAULT_DB_PATH)
            # List all .csv files in the directory
            csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
            return csv_files
        except Exception as e:
            logger.error(f"Error getting available CSV files: {str(e)}")
            return []
    
    def load_csv(file_obj, num_rows, selected_columns, current_pos, filter_condition):
        """Load a CSV file and return a preview dataframe together with an updated
        dropdown component for column selection.

        The column list is now sorted alphabetically to make it easier to scan
        and the dropdown is refreshed using gr.Dropdown.update so that both the
        available choices and the currently-selected columns are updated in the
        UI. This fixes issues where the dropdown initially showed no options or
        presented them in an unexpected order.
        """

        # When no file is provided we reset the UI elements.
        if file_obj is None:
            return (
                None,
                gr.update(choices=[], value=[]),
                0,
            )

        try:
            # Use the file path directly since it's from the server's file system
            df = pd.read_csv(file_obj)

            # Sort columns alphabetically for consistent presentation
            all_columns = sorted(df.columns.tolist())

            # If no columns are selected (or file changed), default to showing all
            if not selected_columns or not any(col in all_columns for col in selected_columns):
                selected_columns = all_columns

            # Always keep the order of the user's selection in the preview,
            # but ensure that every selected column exists in the dataframe.
            selected_columns = [c for c in selected_columns if c in all_columns]

            # Reset position when loading a new file
            current_pos = 0

            # Apply filter if provided
            if filter_condition and filter_condition.strip():
                try:
                    df = df.query(filter_condition)
                except Exception as e:
                    logger.error(f"Error applying filter: {str(e)}")
                    gr.Warning(f"Invalid filter condition: {str(e)}")

            # Build the preview dataframe (first page)
            preview_df = df[selected_columns].iloc[current_pos : current_pos + num_rows]

            # Return preview, an UPDATED dropdown component, and the new position
            return (
                preview_df,
                gr.update(choices=all_columns, value=selected_columns),
                current_pos + num_rows,
            )
        except Exception as e:
            logger.error(f"Error loading CSV: {str(e)}")
            return (
                None,
                gr.update(choices=[], value=[]),
                0,
            )
    
    def load_more_rows(file_obj, num_rows, selected_columns, current_pos, filter_condition):
        if file_obj is None:
            return None, current_pos
        try:
            # Use the file path directly since it's from the server's file system
            df = pd.read_csv(file_obj)
            # Get all available columns (alphabetically sorted for consistency)
            all_columns = sorted(df.columns.tolist())
            
            # Ensure selected columns exist in the dataframe
            valid_columns = [col for col in selected_columns if col in all_columns]
            
            # If no valid columns are selected, use all columns
            if not valid_columns:
                valid_columns = all_columns
            
            # Apply filter if provided
            if filter_condition and filter_condition.strip():
                try:
                    df = df.query(filter_condition)
                except Exception as e:
                    logger.error(f"Error applying filter: {str(e)}")
                    gr.Warning(f"Invalid filter condition: {str(e)}")
            
            # Check if we've reached the end of the file
            if current_pos >= len(df):
                return None, current_pos
            
            # Get next batch of rows
            next_batch = df[valid_columns].iloc[current_pos:current_pos + num_rows]
            
            # Update position
            new_pos = current_pos + num_rows
            
            return next_batch, new_pos
        except Exception as e:
            logger.error(f"Error loading more rows: {str(e)}")
            return None, current_pos
    
    def update_preview(file_obj, num_rows, selected_columns, current_pos, filter_condition):
        if file_obj is None:
            return None, current_pos
        try:
            # Use the file path directly since it's from the server's file system
            df = pd.read_csv(file_obj)
            # Get all available columns (alphabetically sorted for consistency)
            all_columns = sorted(df.columns.tolist())
            
            # Ensure selected columns exist in the dataframe
            valid_columns = [col for col in selected_columns if col in all_columns]
            
            # If no valid columns are selected, use all columns
            if not valid_columns:
                valid_columns = all_columns
            
            # Apply filter if provided
            if filter_condition and filter_condition.strip():
                try:
                    df = df.query(filter_condition)
                except Exception as e:
                    logger.error(f"Error applying filter: {str(e)}")
                    gr.Warning(f"Invalid filter condition: {str(e)}")
            
            # Reset position when changing preview settings
            current_pos = 0
            
            # Filter columns and get preview
            preview_df = df[valid_columns].iloc[current_pos:current_pos + num_rows]
            
            # Update position
            new_pos = current_pos + num_rows
            
            return preview_df, new_pos
        except Exception as e:
            logger.error(f"Error updating preview: {str(e)}")
            return None, current_pos
    
    # Update handlers
    csv_file.choices = get_available_csv_files()  # Set initial choices
    csv_file.change(
        load_csv,
        inputs=[csv_file, preview_rows, column_selector, current_position, filter_input],
        outputs=[csv_preview, column_selector, current_position]
    )
    
    preview_rows.change(
        update_preview,
        inputs=[csv_file, preview_rows, column_selector, current_position, filter_input],
        outputs=[csv_preview, current_position]
    )
    
    column_selector.change(
        update_preview,
        inputs=[csv_file, preview_rows, column_selector, current_position, filter_input],
        outputs=[csv_preview, current_position]
    )
    
    filter_input.change(
        update_preview,
        inputs=[csv_file, preview_rows, column_selector, current_position, filter_input],
        outputs=[csv_preview, current_position]
    )
    
    load_more_btn.click(
        load_more_rows,
        inputs=[csv_file, preview_rows, column_selector, current_position, filter_input],
        outputs=[csv_preview, current_position]
    )
    
    # Add handlers for prompt template editing
    def update_prompt_editor(prompt_file):
        return load_prompt_template(prompt_file)
    
    def save_prompt(prompt_file, content):
        success = save_prompt_template(prompt_file, content)
        if success:
            gr.Info("Prompt template saved successfully!")
        else:
            gr.Error("Error saving prompt template!")
        return content  # Return the content to keep it in the editor
    
    prompt_dropdown.change(
        update_prompt_editor,
        inputs=[prompt_dropdown],
        outputs=[prompt_editor]
    )
    
    save_prompt_btn.click(
        save_prompt,
        inputs=[prompt_dropdown, prompt_editor],
        outputs=[prompt_editor]  # Keep the content in the editor
    )
    
    msg.submit(
        process_message,
        [
            msg,
            chatbot,
            architecture_dropdown,
            model_dropdown,
            include_cheatsheet,
            include_schema,
            retriever_dropdown,
            prompt_dropdown,
            temperature,
            top_p,
            top_k,
            max_steps_slider,  # NEW
            pydough_tool,
            sql_list_tables,
            sql_schema,
            sql_query,
            sql_query_checker,
            document_kb,
            db_dropdown,
            use_sh_query_gen_chk,
        ],
        [chatbot],
    )
    clear.click(lambda: None, None, chatbot, queue=False)

# Mount Gradio app to FastAPI
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    # Enable auto-reload for easier development when the environment variable is set (default: enabled)
    AUTO_RELOAD = os.getenv("AUTO_RELOAD", "true").lower() in ("1", "true", "yes")

    if AUTO_RELOAD:
        logger.info("Starting server on port 2024 with auto-reload enabled")
        # Run Uvicorn with reload so that changes to the source code are picked up automatically.
        # We pass the application as an import string so that the reloader can properly watch files.
        uvicorn.run(
            "generator_team.servers.gradio_server:app",  # module:variable reference
            host="127.0.0.1",#"0.0.0.0",
            port=2024,
            reload=True,
        )
    else:
        logger.info("Starting server on port 2024 (auto-reload disabled)")
        public_url = demo.launch(
            share=True,
            server_name="127.0.0.1",
            server_port=2024,
            show_error=True,
            show_api=False,
        )
        # print("\n" + "="*50)
        # print(f"Public Gradio URL: {public_url}")
        # print("="*50 + "\n") 