import pandas as pd
import os
import sys # Import sys module
import time
import argparse
from io import StringIO
from tqdm import tqdm
import re
import importlib.util # Added for dynamic agent loading

# ---------------------------------------------------------------------------
# Early environment configuration *before* any library that may auto-instrument
# OpenTelemetry (e.g., `openinference.instrumentation.langchain`) gets imported.
# This ensures the first created TracerProvider/exporter already points to the
# Phoenix collector rather than the default localhost:4317.
# ----------------------------------------------------------------------------
from dotenv import load_dotenv
load_dotenv()

# Use Phoenix by default unless USE_MLFLOW is explicitly set to a truthy value
USE_MLFLOW_ENV = os.getenv("USE_MLFLOW", "false").lower()
USE_MLFLOW = USE_MLFLOW_ENV in ("1", "true", "yes")

# If we are NOT using MLflow, prepare OpenTelemetry env vars for Phoenix **now**
if not USE_MLFLOW:
    API_KEY = os.getenv("PHOENIX_API_KEY", "")
    COLLECTOR_ENDPOINT = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "")

    if COLLECTOR_ENDPOINT:
        # Point the OTLP exporter to Phoenix HTTP endpoint and force HTTP/Protobuf
        os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", COLLECTOR_ENDPOINT)
        os.environ.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf")
    if API_KEY:
        os.environ.setdefault("OTEL_EXPORTER_OTLP_HEADERS", f"Authorization=Bearer {API_KEY}")

# ---------------------------------------------------------------------------

# For Phoenix, explicitly register a tracer provider *before* any auto
# instrumentation kicks in, so that later calls do not need to override it.
if not USE_MLFLOW and os.getenv("PHOENIX_COLLECTOR_ENDPOINT"):
    from phoenix.otel import register  # local import to avoid cost if MLflow mode
    tracer_provider = register(
        endpoint=os.getenv("PHOENIX_COLLECTOR_ENDPOINT"),
        headers={"Authorization": f"Bearer {os.getenv('PHOENIX_API_KEY', '')}"},
        project_name=os.getenv("EXPERIMENT_NAME", "agent-arch-eval"),
        auto_instrument=True,
        protocol="http/protobuf",
    )

# ---------------------------------------------------------------------------

# Import modules that may trigger OpenTelemetry instrumentation AFTER env vars
# are set, so they pick up the correct collector configuration.

from generator_team.agents.ReAct import PydoughGeneratorAgent
from generator_team.agents.evaluator_agent import SQLEvaluatorAgent, compare_df
import json

# Global variable to control logging backend
USE_MLFLOW = False  # Set to False to use Phoenix instead

# Configure MLflow
if USE_MLFLOW:
    import mlflow
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    MLFLOW_TRACKING_TOKEN = os.getenv("MLFLOW_TRACKING_TOKEN", "")
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(os.getenv("EXPERIMENT_NAME", "agent-playground"))
    # Enable MLflow LangChain autologging
    mlflow.langchain.autolog(
        log_traces=True,
        log_models=True,
        log_input_examples=True,
        log_model_signatures=True,
        registered_model_name="pydough_agent",
    )
else:
    # Tracer provider already registered above; nothing further required here.
    pass

# Available models for the generator agent
MODELS =["projects/316936339319/locations/us-central1/endpoints/4491730399348654080",
         "gemini-2.0-flash"]

# Global path configurations (adapted from gradio_server.py)
_CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(_CURRENT_FILE_DIR) # This should be /c/Users/david/bodo (parent of generator_team)
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

def convert_windows_to_wsl_path(windows_path: str) -> str:
    """Convert a Windows path to a WSL path **only** when running inside WSL.

    If the current runtime is Windows (`os.name == 'nt'`), we keep the path in
    Windows format but normalise the directory separators to forward slashes so
    that SQLAlchemy (and other URI consumers) can still parse it correctly.

    When the runtime is Linux/WSL (`os.name != 'nt'`) and the incoming path
    contains a Windows drive letter, we convert it to the corresponding
    `/mnt/<drive>/` location that WSL expects.
    """
    # Normalise path separators first – this is harmless on both OSes
    windows_path = windows_path.replace('\\', '/')

    # If we're running on Windows we *do not* convert to the /mnt style – return
    # the normalised path as-is so that native Windows Python can open the file.
    if os.name == 'nt':
        return windows_path

    # On non-Windows (e.g. WSL/Linux) convert a drive-prefixed path (e.g.
    # `C:/Users/...`) to `/mnt/c/Users/...` so that it resolves inside the WSL
    # filesystem. If there is no drive letter just return the normalised path
    # unchanged.
    if ':' in windows_path:
        drive, path_part = windows_path.split(':', 1)
        drive = drive.lower()
        return f"/mnt/{drive}{path_part}"

    return windows_path

def get_defog_dataset_paths(dataset_name: str) -> tuple[str, str]:
    """
    Resolve the absolute paths of the **Defog** database file and its metadata
    JSON, given *dataset_name* which can be provided in several formats:

    1. Just the bare dataset identifier – e.g. ``"Broker"``.
    2. A filename such as ``"Broker.sqlite"`` or ``"Broker.db"``.
    3. A *relative* or *absolute* path that already points to the ``.sqlite``/
       ``.db`` file (for example ``"Defog/databases/Broker/Broker.sqlite"``).

    The function normalises all of these inputs and returns a tuple of strings
    ``(db_path, metadata_path)`` suitable for further processing.  Both paths
    are converted via ``convert_windows_to_wsl_path`` so they work on the
    current host OS.
    """
    # ------------------------------------------------------------------
    # 1) If the caller already passed a path that exists on disk we can use it
    #    directly and merely derive the dataset *name* for the metadata file.
    # ------------------------------------------------------------------
    candidate = os.path.normpath(dataset_name)
    if os.path.isabs(candidate) or os.path.sep in candidate:
        if os.path.exists(candidate):
            # e.g. C:/…/Defog/databases/Broker/Broker.sqlite – use as-is.
            db_path = candidate
            base_name = os.path.splitext(os.path.basename(candidate))[0]
            metadata_path = os.path.join(WORKSPACE_ROOT, "Defog", "metadata", f"{base_name}_graph.json")
            if not os.path.exists(metadata_path):
                raise FileNotFoundError(f"Metadata file not found at {metadata_path}")
            return convert_windows_to_wsl_path(db_path), convert_windows_to_wsl_path(metadata_path)
        # If it *looks* like a path but doesn't exist we'll fall through to the
        # standard search places below.

    # ------------------------------------------------------------------
    # 2) The caller provided only the dataset identifier (optionally with file
    #    extension) – canonicalise to the bare name, e.g. "Broker".
    # ------------------------------------------------------------------
    bare_name = os.path.splitext(os.path.basename(dataset_name))[0]

    defog_db_dir_abs = os.path.join(WORKSPACE_ROOT, "Defog", "databases")
    defog_metadata_dir_abs = os.path.join(WORKSPACE_ROOT, "Defog", "metadata")

    # Possible database filenames we want to check, in order of preference.
    db_filenames = [f"{bare_name}.sqlite", f"{bare_name}.db"]

    # 2a) Nested directory structure: Defog/databases/<name>/<name>.(sqlite|db)
    for fname in db_filenames:
        potential_db_path = os.path.join(defog_db_dir_abs, bare_name, fname)
        potential_metadata_path = os.path.join(defog_metadata_dir_abs, f"{bare_name}_graph.json")
        if os.path.exists(potential_db_path) and os.path.exists(potential_metadata_path):
            return (
                convert_windows_to_wsl_path(potential_db_path),
                convert_windows_to_wsl_path(potential_metadata_path),
            )

    # 2b) Flat directory structure: Defog/databases/<name>.(sqlite|db)
    for fname in db_filenames:
        potential_db_path = os.path.join(defog_db_dir_abs, fname)
        potential_metadata_path = os.path.join(defog_metadata_dir_abs, f"{bare_name}_graph.json")
        if os.path.exists(potential_db_path) and os.path.exists(potential_metadata_path):
            return (
                convert_windows_to_wsl_path(potential_db_path),
                convert_windows_to_wsl_path(potential_metadata_path),
            )

    # If we reach this point we couldn't resolve the dataset.
    raise FileNotFoundError(
        f"Defog dataset '{dataset_name}' not found. Tried variations under:\n"
        f"  - {defog_db_dir_abs}/<name>/<name>.sqlite|db\n"
        f"  - {defog_db_dir_abs}/<name>.sqlite|db\n"
        f"with corresponding metadata in {defog_metadata_dir_abs}"
    )

def process_single_question(
    question: str,
    sql_query: str,
    generator_agent: PydoughGeneratorAgent,
    evaluator_agent: SQLEvaluatorAgent,
    question_id: int,
    pbar: tqdm,
    agent_type: str
) -> dict:
    """
    Process a single question sequentially.
    """
    print("\n" + "="*50, flush=True)
    print(f"STARTING PROCESSING FOR QUESTION {question_id} (Agent Type: {agent_type.upper()})", flush=True)
    print("="*50 + "\n", flush=True)
    
    # Initialize result variables
    evaluation = {'match': None, 'explanation': None}
    generated_response = ''
    generated_pydough = ''
    generated_sql = '' # New: for SQL agents
    executor_error = None
    generated_df_json = '{}' # Default to empty JSON for DataFrame
    
    try:
        # Execute the ground truth SQL query
        sql_result_json = evaluator_agent._convert_sql_to_dataframe(sql_query) # Returns JSON string
        ground_truth_df = pd.read_json(StringIO(sql_result_json))
        
        print("\n" + "-"*50, flush=True)
        print(f"GENERATOR CALL ({agent_type.upper()})", flush=True)
        print("-"*50 + "\n", flush=True)
        
        print(f"Question: {question}")

        generated_code_output = None # To store output from agent.generate_and_execute or agent.ask

        if agent_type == "pydough":
            # Generate Pydough code and execute
            generated_code_output = generator_agent.generate_and_execute(question)
            
            print("\nGENERATOR RESPONSE (Pydough):", flush=True)
            print(f"Type: {type(generated_code_output)}", flush=True)
            print(f"Keys: {generated_code_output.keys() if isinstance(generated_code_output, dict) else 'Not a dict'}", flush=True)
            print(f"Full response: {generated_code_output}", flush=True)
            
            generated_response = generated_code_output.get('generator_response', generated_code_output.get('answer', '')) # PydoughGeneratorAgent uses 'answer'
            generated_df_json = generated_code_output.get('dataframe', '{}')
            generated_pydough = generated_code_output.get('pydough_code', '')

            if not generated_pydough and generated_response:
                print("\nATTEMPTING TO EXTRACT PYDOUGH CODE:", flush=True)
                code_match = re.search(r'```python\n(.*?)\n```', generated_response, re.DOTALL)
                if code_match:
                    generated_pydough = code_match.group(1).strip()
                    print(f"Extracted code: {generated_pydough}", flush=True)
                else:
                    print("No PyDough code block found in response", flush=True)
                    # Keep generated_pydough as is, could be set by agent directly
            
        elif agent_type == "sql":
            # Execute SQL agent (e.g., SelfHealingSQLAgent)
            # Assuming it has an 'ask' method or similar that returns a state/dict
            # The actual method and return structure might differ for SelfHealingSQLAgent
            if hasattr(generator_agent, 'ask'):
                 # This is the expected path for SelfHealingSQLAgent based on gradio_server.py
                agent_state = generator_agent.ask(question) 
                
                print("\nGENERATOR RESPONSE (SQL Agent State):", flush=True)
                print(f"Type: {type(agent_state)}", flush=True)
                print(f"Full state/response: {agent_state}", flush=True)

                # Extract relevant info from the state
                # Based on SelfHealingSQLAgent structure in gradio_server.py:
                # state often contains 'messages' list, where the last message is the answer.
                # The 'answer' might be the final SQL or a natural language response.
                # It might also contain 'final_generated_sql' or similar.
                
                # Attempt to get the final SQL query
                final_sql_query_candidate = agent_state.get("final_generated_sql")
                if not final_sql_query_candidate and isinstance(agent_state.get("messages"), list) and agent_state["messages"]:
                    # Check last message content for SQL
                    last_message_content = agent_state["messages"][-1].content
                    sql_match = re.search(r"```sql\n(.*?)\n```", last_message_content, re.DOTALL)
                    if sql_match:
                        final_sql_query_candidate = sql_match.group(1).strip()
                    else: # if no SQL block, assume the content IS the SQL or NL response
                        final_sql_query_candidate = last_message_content

                generated_sql = final_sql_query_candidate if final_sql_query_candidate else "No SQL Generated"
                
                # The 'answer' or 'result_df' might be directly in the state, or we execute the SQL
                # For now, let's assume we always try to execute the generated_sql
                generated_response = agent_state.get("answer", generated_sql) # Or some other key for NL response

                if generated_sql and generated_sql != "No SQL Generated" and not agent_state.get("result_df"):
                    print(f"\nExecuting generated SQL: {generated_sql}", flush=True)
                    try:
                        # Use the evaluator_agent to run the SQL and get DataFrame JSON
                        generated_df_json_str = evaluator_agent._convert_sql_to_dataframe(generated_sql)
                        generated_df_json = generated_df_json_str # Store JSON string
                    except Exception as exec_e:
                        print(f"Error executing generated SQL: {str(exec_e)}", flush=True)
                        executor_error = f"Error executing generated SQL: {str(exec_e)}"
                        generated_df_json = "{}" # Ensure it's a valid JSON string for an empty df
                elif agent_state.get("result_df") is not None: # If agent returns DataFrame directly
                    df_result = agent_state.get("result_df")
                    if isinstance(df_result, pd.DataFrame):
                         generated_df_json = df_result.to_json(orient="records", indent=4)
                    elif isinstance(df_result, str): # Assuming it's already JSON
                         generated_df_json = df_result
                    else:
                         print(f"Warning: result_df is of unexpected type: {type(df_result)}", flush=True)
                         generated_df_json = "{}"

            elif hasattr(generator_agent, 'generate_and_execute'): # Fallback if it's like PydoughGeneratorAgent
                generated_code_output = generator_agent.generate_and_execute(question) # This might not be standard for all SQL agents
                generated_response = generated_code_output.get('answer', '') # Or 'generator_response'
                # If the SQL agent returns SQL, we might need to execute it here
                generated_sql = generated_code_output.get('sql_query', generated_code_output.get('generated_sql','')) # Key might vary
                generated_df_json = generated_code_output.get('dataframe', '{}') # If agent executes and returns df
                
                if generated_sql and not generated_df_json and generated_df_json == '{}': # If SQL is there but no df
                    try:
                        generated_df_json_str = evaluator_agent._convert_sql_to_dataframe(generated_sql)
                        generated_df_json = generated_df_json_str
                    except Exception as exec_e:
                        executor_error = f"Error executing generated SQL: {str(exec_e)}"
                        generated_df_json = "{}"
            else:
                raise NotImplementedError(f"SQL Agent {type(generator_agent)} does not have 'ask' or 'generate_and_execute' method.")

        print("\nEXTRACTED VALUES:", flush=True)
        print(f"Generated response: {generated_response}", flush=True)
        if agent_type == "pydough":
            print(f"Generated PyDough: {generated_pydough}", flush=True)
        elif agent_type == "sql":
            print(f"Generated SQL: {generated_sql}", flush=True)
        print(f"DataFrame JSON: {generated_df_json}", flush=True)
        
        # If we don't have the PyDough code (pydough agent) and generated_response has it
        if agent_type == "pydough" and not generated_pydough and generated_response:
            print("\nATTEMPTING TO EXTRACT PYDOUGH CODE (again, if missed):", flush=True)
            code_match = re.search(r'```python\n(.*?)\n```', generated_response, re.DOTALL)
            if code_match:
                generated_pydough = code_match.group(1).strip()
                print(f"Extracted code: {generated_pydough}", flush=True)
            # else:
                # print("No code block found in response", flush=True)
                # generated_pydough = "No Parsable Code Found" # Avoid overwriting if agent did set it
                # generated_response = "No Parsable Code Found"
                # generated_df_json = "{}"

        # If we don't have the SQL code (sql agent) and generated_response has it (e.g. NL response with SQL block)
        if agent_type == "sql" and not generated_sql and generated_response:
            print("\nATTEMPTING TO EXTRACT SQL CODE FROM RESPONSE:", flush=True)
            code_match = re.search(r'```sql\n(.*?)\n```', generated_response, re.DOTALL)
            if code_match:
                generated_sql = code_match.group(1).strip()
                print(f"Extracted SQL: {generated_sql}", flush=True)
                # If SQL extracted and dataframe not yet populated, try to execute
                if generated_df_json == '{}' and not executor_error:
                    try:
                        generated_df_json_str = evaluator_agent._convert_sql_to_dataframe(generated_sql)
                        generated_df_json = generated_df_json_str
                    except Exception as exec_e:
                        executor_error = f"Error executing extracted SQL: {str(exec_e)}"
                        generated_df_json = "{}"
            # else:
                # print("No SQL block found in response", flush=True)

        # Check if we got a valid result dataframe
        generated_df = pd.DataFrame() # Initialize empty
        if generated_df_json and generated_df_json != '{}':
            try:
                # Ensure generated_df_json is a string before passing to StringIO
                if not isinstance(generated_df_json, str):
                    print(f"Warning: generated_df_json is not a string, type: {type(generated_df_json)}. Attempting to convert.", flush=True)
                    # Attempt to convert common non-string outputs to JSON string
                    if isinstance(generated_df_json, pd.DataFrame): # Should not happen here, but as a safeguard
                        generated_df_json = generated_df_json.to_json(orient="records", indent=4)
                    elif isinstance(generated_df_json, dict) or isinstance(generated_df_json, list):
                        generated_df_json = json.dumps(generated_df_json)
                    else: # Fallback if conversion is unknown
                        raise ValueError(f"Cannot convert type {type(generated_df_json)} to JSON string for pd.read_json")

                generated_df = pd.read_json(StringIO(generated_df_json))
            except Exception as e:
                # If executor_error is already set, don't overwrite it with JSON parsing error unless it's None
                if not executor_error:
                    executor_error = f"Error parsing DataFrame JSON: {str(e)}. JSON: '{generated_df_json[:200]}...'"
                print(f"DataFrame parsing error: {executor_error}", flush=True)
                generated_df = pd.DataFrame() # Ensure it's an empty DataFrame on error
        elif not generated_df_json or generated_df_json == '{}': # Explicitly handle empty JSON string
             print("Generated DataFrame JSON is empty or None. Using empty DataFrame.", flush=True)
             generated_df = pd.DataFrame()


        print("\nDATAFRAME STATUS:", flush=True)
        print(f"Shape: {generated_df.shape}", flush=True)
        print(f"Error during DataFrame generation/parsing (if any): {executor_error}", flush=True)
        
        # Compare the dataframes
        dataframe_comparison_boolean = compare_df(
            ground_truth_df,
            generated_df,
            "order_by", # This might need to be configurable or handled differently based on agent/question
            question
        )
        
        # Get evaluation from evaluator
        evaluation = evaluator_agent.evaluate_responses(
            question=question,
            ground_truth_sql=sql_query,
            generated_response=generated_response,
            generated_df_json=generated_df_json if isinstance(generated_df_json, str) else "{}", # Ensure it's a string
            precomputed_match=dataframe_comparison_boolean,
            executor_error=executor_error
        )
        
    except Exception as e:
        print("\nPROCESSING ERROR:", flush=True)
        print(f"Error: {str(e)}", flush=True)
        # Ensure traceback is printed for debugging
        import traceback
        traceback.print_exc()
        result = {
            'question_id': question_id,
            'question': question,
            'ground_truth_sql': sql_query,
            'generated_response': generated_response,
            'generated_pydough': generated_pydough if agent_type == "pydough" else None,
            'generated_sql': generated_sql if agent_type == "sql" else None,
            'evaluation_match': evaluation.get('match'), # Use .get for safety
            'evaluation_explanation': evaluation.get('explanation'), # Use .get for safety
            'dataframe_match': False, # Default on error
            'error': str(e)
        }
        return result
    
    # Store results
    result = {
        'question_id': question_id,
        'question': question,
        'ground_truth_sql': sql_query,
        'generated_response': generated_response,
        'generated_pydough': generated_pydough if agent_type == "pydough" else None,
        'generated_sql': generated_sql if agent_type == "sql" else None,
        'evaluation_match': evaluation['match'],
        'evaluation_explanation': evaluation['explanation'],
        'dataframe_match': dataframe_comparison_boolean,
        'error': executor_error # Store executor_error here, or None if main try block succeeded
    }
    
    print("\n" + "="*50, flush=True)
    print("FINAL RESULT:", flush=True)
    print(f"Generated response: {result['generated_response']}", flush=True)
    if agent_type == "pydough":
        print(f"Generated PyDough: {result['generated_pydough']}", flush=True)
    elif agent_type == "sql":
        print(f"Generated SQL: {result['generated_sql']}", flush=True)
    print("="*50 + "\n", flush=True)
    
    return result

def process_questions(
    questions_csv_path: str,
    output_csv_path: str,
    db_path: str,
    metadata_path: str,
    cheatsheet_path: str,
    num_questions: int = None,
    start_row: int = 0,
    model_name: str = None,
    agent_type: str = "pydough",
    agent_path: str = None,
    filter_query_errors: bool = True,
    error_keyword: str = "Query Error",
    temperature: float = 0.3
) -> None:
    """
    Process questions from CSV and store results in output CSV sequentially.
    `db_path`, `metadata_path` here are global fallbacks if not specified in CSV.
    """
    print(f"\nOutput will be saved to: {output_csv_path}")
    print(f"Global fallback DB path: {db_path}")
    print(f"Global fallback Metadata path: {metadata_path}")
    print(f"Filtering for Query Errors: {filter_query_errors}")

    # Initialize agents - these will be potentially re-initialized if CSV specifies per-row dataset
    current_generator_agent = None
    current_evaluator_agent = None
    active_db_path = None
    active_metadata_path = None

    pbar = None  # Will hold the tqdm progress bar once it is created

    def _init_agents(use_db_path, use_metadata_path, cheatsheet_path, model_name, agent_type, agent_path, temperature):
        print(f"Initializing agents with DB: {use_db_path}, Metadata: {use_metadata_path}")
        local_generator_agent = None
        if agent_type == "pydough":
            local_generator_agent = PydoughGeneratorAgent(
                db_path=use_db_path,
                metadata_path=use_metadata_path,
                cheatsheet_path=cheatsheet_path, # Cheatsheet is global for now
                model_name=model_name,
                temperature=temperature
            )
        elif agent_type == "sql":
            if not agent_path:
                raise ValueError("agent_path must be provided for SQL agent type.")

            full_agent_path = os.path.join(WORKSPACE_ROOT, agent_path)

            # -------------------------------------------------- dynamic import logic (restored) START
            # Try to import the module using its dotted path first to avoid loading
            # the same file twice under different names, which can break type
            # resolution. Fallback to importlib.util when the dotted-path import
            # fails (e.g. when the file is outside a package).
            rel_path = os.path.relpath(full_agent_path, WORKSPACE_ROOT)
            dotted_path = os.path.splitext(rel_path)[0].replace(os.path.sep, ".")

            try:
                agent_module = importlib.import_module(dotted_path)
            except Exception:
                spec = importlib.util.spec_from_file_location(os.path.splitext(os.path.basename(agent_path))[0], full_agent_path)
                if spec is None:
                    raise ImportError(f"Could not load spec for module at {full_agent_path}")
                agent_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(agent_module)  # type: ignore[arg-type]
            # -------------------------------------------------- dynamic import logic END

            # Infer the agent class name
            if hasattr(agent_module, "SelfHealingSQLAgent"):
                class_name_candidate = "SelfHealingSQLAgent"
            else:
                class_name_base = os.path.splitext(os.path.basename(agent_path))[0]
                class_name_candidate = class_name_base + "Agent" if "Agent" not in class_name_base else class_name_base

            if not hasattr(agent_module, class_name_candidate):
                raise ImportError(f"Agent class '{class_name_candidate}' not found in {full_agent_path}.")

            AgentClass = getattr(agent_module, class_name_candidate)

            # Instantiate the SQL generator agent (constructor may vary across
            # implementations – we supply the DB path and model name which are
            # common to all agents in this repo).
            local_generator_agent = AgentClass(
                db_path=use_db_path,
                model_name=model_name,
                temperature=temperature
            )
        else:
            raise ValueError(f"Unsupported agent_type: {agent_type}")

        # Evaluator always initialises from the *current* DB path
        local_evaluator_agent = SQLEvaluatorAgent(f"sqlite:///{use_db_path}")

        return local_generator_agent, local_evaluator_agent

    try:
        # Read the CSV file
        df = pd.read_csv(questions_csv_path)
        
        # Filter the DataFrame if num_questions is specified
        if num_questions is not None:
            df = df.iloc[start_row:start_row+num_questions]
        else:
            df = df.iloc[start_row:]

        # ------------------------------------------------------------------
        # Pre-filter rows based on comparison_result/comparison_result_opus if
        # the user wants to focus only on "Query Error" cases.
        # ------------------------------------------------------------------
        if filter_query_errors and {'comparison_result','comparison_result_opus'} <= set(df.columns):
            query_error_clean = error_keyword.strip()
            mask = (
                df['comparison_result'].fillna('').astype(str).str.strip().eq(query_error_clean)
            ) & (
                df['comparison_result_opus'].fillna('').astype(str).str.strip().eq(query_error_clean)
            )
            original_len = len(df)
            df_filtered = df[mask].copy()
            print(f"Pre-filtering rows for '{error_keyword}' reduced the dataset from {original_len} to {len(df_filtered)} rows.")
            if len(df_filtered) == 0:
                print("[warning] No rows match the requested error filter – proceeding with **all** selected rows instead.")
            else:
                df = df_filtered
        
        # Initialize progress bar
        pbar = tqdm(total=len(df), desc="Processing questions")
        
        # Initialize output data list
        output_data = []
        
        for idx, row in df.iterrows():
            question = row['question']
            sql_query = row['sql']
            
            # Start with the global defaults – these may be overridden below
            question_db_path = db_path
            question_metadata_path = metadata_path

            # --------------------------------------------------------------
            # Resolve dataset / metadata for *this* question.
            # Priority order:
            #   1. Explicit `db_path` / `metadata_path` columns (absolute or
            #      relative paths) – if present and non-empty.
            #   2. Logical name in `db_name` column (e.g. "Broker") – looked up
            #      via get_defog_dataset_paths.
            #   3. Legacy `dataset_name` column – looked up the same way.
            #   4. Fallback to the global CLI-supplied paths.
            # --------------------------------------------------------------
            if 'db_path' in row and pd.notna(row['db_path']) and str(row['db_path']).strip():
                question_db_path = str(row['db_path']).strip()
            if 'metadata_path' in row and pd.notna(row.get('metadata_path')) and str(row['metadata_path']).strip():
                question_metadata_path = str(row['metadata_path']).strip()

            # Use db_name if explicit paths were not provided
            if question_db_path == db_path and 'db_name' in row and pd.notna(row['db_name']) and str(row['db_name']).strip():
                name = str(row['db_name']).strip()
                print(f"\nProcessing Question ID {idx+1} with db_name from CSV: '{name}'")
                try:
                    question_db_path, question_metadata_path = get_defog_dataset_paths(name)
                except FileNotFoundError as e:
                    print(f"Warning: Defog dataset '{name}' for Question ID {idx+1} not found. Error: {e}. Using fallback DB.")

            # Use dataset_name as a last resort for backwards compatibility
            if question_db_path == db_path and 'dataset_name' in row and pd.notna(row['dataset_name']) and str(row['dataset_name']).strip():
                name = str(row['dataset_name']).strip()
                print(f"\nProcessing Question ID {idx+1} with dataset_name from CSV: '{name}'")
                try:
                    question_db_path, question_metadata_path = get_defog_dataset_paths(name)
                except FileNotFoundError as e:
                    print(f"Warning: Defog dataset '{name}' for Question ID {idx+1} not found. Error: {e}. Using fallback DB.")

            # If we still don't have a DB path, skip this row gracefully
            if not question_db_path:
                print(f"Warning: No database resolved for question {idx+1}; skipping.")
                continue

            # Initialize agents
            if current_generator_agent is None or active_db_path != question_db_path:
                print(f"Dataset changed or first run. Old DB: {active_db_path}, New DB: {question_db_path}. Re-initializing agents.")
                current_generator_agent, current_evaluator_agent = _init_agents(
                    question_db_path, 
                    question_metadata_path, 
                    cheatsheet_path, 
                    model_name, 
                    agent_type, 
                    agent_path,
                    temperature
                )
                active_db_path = question_db_path
                active_metadata_path = question_metadata_path # Track active metadata too
            
            # Ensure agents are initialized if they are somehow still None (should not happen with above logic)
            if current_generator_agent is None or current_evaluator_agent is None:
                 print("Error: Agents are not initialized. Forcing initialization with fallback paths.")
                 current_generator_agent, current_evaluator_agent = _init_agents(
                    question_db_path, question_metadata_path, cheatsheet_path, model_name, agent_type, agent_path, temperature
                 )
                 active_db_path = question_db_path
                 active_metadata_path = question_metadata_path

            result = process_single_question(
                question=row['question'],
                sql_query=row['sql'],
                generator_agent=current_generator_agent,
                evaluator_agent=current_evaluator_agent, # Pass the potentially re-initialized evaluator
                question_id=idx + 1,
                pbar=pbar,
                agent_type=agent_type,
                # Optional: pass current_db_path if process_single_question needs it for other reasons
                # current_db_path=active_db_path 
            )
            
            # Merge original CSV columns with the generated result so that all source fields are preserved
            # Row is a pandas Series; convert it to a plain dict for merging.
            original_row_data = row.to_dict()

            # Combine dictionaries: original CSV fields first, then our generated result to ensure
            # that keys like 'generated_response' override any potential name collisions (e.g., 'question').
            combined_result = {**original_row_data, **result}

            # Overwrite / add a unified comparison_result so later filters work
            if result.get("error"):
                combined_result["comparison_result"] = "Query Error"
            else:
                combined_result["comparison_result"] = "Match" if result["evaluation_match"] else "No Match"

            output_data.append(combined_result)
            pbar.update(1)
            
            # Save progress after each result
            df = pd.DataFrame(output_data)
            
            # Filter for Query Errors if requested
            if filter_query_errors and {'comparison_result','comparison_result_opus'} <= set(df.columns):
                print("\n=== Filtering Results (preview only, original rows kept) ===")
                query_error_clean = error_keyword.strip()
                mask = (
                    df['comparison_result'].fillna('').astype(str).str.strip().eq(query_error_clean)
                ) & (
                    df['comparison_result_opus'].fillna('').astype(str).str.strip().eq(query_error_clean)
                )
                filtered_df = df[mask]
                print(f"Total rows: {len(df)}  |  Rows matching \"{error_keyword}\": {len(filtered_df)}")
                if len(filtered_df) > 0:
                    print(filtered_df[['comparison_result','comparison_result_opus']].head())
            
            print("\n=== Writing to CSV ===")
            print(f"DataFrame columns: {df.columns.tolist()}")
            print(f"Generated response: {result['generated_response']}")
            if agent_type == "pydough":
                print(f"Generated PyDough: {result['generated_pydough']}")
            elif agent_type == "sql":
                print(f"Generated SQL: {result['generated_sql']}")
            print(f"DataFrame shape: {df.shape}")
            
            # Save to CSV
            df.to_csv(output_csv_path, index=False)
            
            # Verify the saved data
            saved_df = pd.read_csv(output_csv_path)
            print("\n=== Verifying Saved Data ===")
            print(f"Saved DataFrame columns: {saved_df.columns.tolist()}")

            if len(saved_df) == 0:
                print("[info] CSV currently contains 0 rows after filtering – skipping row verification.")
            else:
                print(f"Last row generated response: {saved_df.iloc[-1]['generated_response']}")
                if agent_type == "pydough":
                    print(f"Last row generated PyDough: {saved_df.iloc[-1]['generated_pydough']}")
                elif agent_type == "sql":
                    print(f"Last row generated SQL: {saved_df.iloc[-1]['generated_sql']}")
            
            # Debug print the saved data
            print(f"\nSaved data to CSV. Response: {result['generated_response']}")
            if agent_type == "pydough":
                print(f"PyDough code: {result['generated_pydough']}")
            elif agent_type == "sql":
                print(f"SQL code: {result['generated_sql']}")
    
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        raise
    finally:
        # Only attempt to close the progress bar if it was actually created
        if pbar is not None:
            pbar.close()

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process questions using PyDough generator agent sequentially.')
    parser.add_argument('--num-questions', type=int, default=None,
                      help='Number of questions to process (default: all)')
    parser.add_argument('--start-row', type=int, default=0,
                      help='Row number to start processing from (0-based index, default: 0)')
    parser.add_argument('--output-dir', type=str, default=None,
                      help='Directory to save output files (default: labeling_agent/results)')
    parser.add_argument('--db-path', type=str, default="",
                      help='Global fallback SQLite database file (optional; per-row values preferred)')
    parser.add_argument('--metadata-path', type=str, default="",
                      help='Global fallback metadata graph JSON file (optional)')
    parser.add_argument('--cheatsheet-path', type=str, required=True,
                      help='Path to the cheatsheet markdown file')
    parser.add_argument('--questions-csv-path', type=str, required=True,
                      help='Path to the questions CSV file')
    parser.add_argument('--model-name', type=str, default=MODELS[0],
                      help=f'Name of the model to use (default: {MODELS[0]}). Available models: {", ".join(MODELS)}')
    parser.add_argument('--agent-type', type=str, default="pydough", choices=["pydough", "sql"],
                      help='Type of agent to run (default: pydough)')
    parser.add_argument('--agent-path', type=str, default=None,
                      help='Path to the custom agent Python file (e.g., generator_team/agents/MyAgent.py). Required if agent-type is not pydough.')
    parser.add_argument('--dataset-name', type=str, default=None,
                      help='Name of the Defog dataset to use (e.g., "Broker"). If provided, overrides db-path and metadata-path for Defog datasets.')
    parser.add_argument('--filter-query-errors', type=str, default="true",
                      help='Filter results to only include rows where both comparison_result and comparison_result_opus are "Query Error" (default: true)')
    parser.add_argument('--error-keyword', type=str, default="Query Error",
                      help='Keyword to use for filtering query errors (default: "Query Error")')
    parser.add_argument('--temperature', type=float, default=0.3,
                      help='Temperature for LLM generation (default: 0.3)')
    args = parser.parse_args()
    
    # Set up output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
    
    # Create output filename with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_csv_path = os.path.join(output_dir, f"pydough_results_{timestamp}.csv")
    
    # Determine DB and metadata paths
    db_path_to_use = args.db_path or ""
    metadata_path_to_use = args.metadata_path or ""

    if args.dataset_name:
        print(f"Loading Defog dataset: {args.dataset_name}")
        try:
            db_path_to_use, metadata_path_to_use = get_defog_dataset_paths(args.dataset_name)
            print(f"Using DB: {db_path_to_use}")
            print(f"Using Metadata: {metadata_path_to_use}")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return
    
    # Verify that mandatory resources exist
    mandatory_files = {
        'Cheatsheet': args.cheatsheet_path,
        'Questions CSV': args.questions_csv_path
    }

    for name, path in mandatory_files.items():
        if not os.path.exists(path):
            print(f"Error: {name} file not found at {path}")
            return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert filter-query-errors string to boolean
    filter_query_errors = args.filter_query_errors.lower() in ("true", "1", "yes")
    
    # Process questions
    process_questions(
        questions_csv_path=args.questions_csv_path,
        output_csv_path=output_csv_path,
        db_path=db_path_to_use,
        metadata_path=metadata_path_to_use,
        cheatsheet_path=args.cheatsheet_path,
        num_questions=args.num_questions,
        start_row=args.start_row,
        model_name=args.model_name,
        agent_type=args.agent_type,
        agent_path=args.agent_path,
        filter_query_errors=filter_query_errors,
        error_keyword=args.error_keyword,
        temperature=args.temperature
    )
    
    print(f"\nProcessing complete! Results saved to: {output_csv_path}")

if __name__ == "__main__":
    main() 