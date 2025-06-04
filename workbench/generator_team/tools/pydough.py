from typing import Dict, Any, Optional, Tuple
from langchain.tools import BaseTool
from langchain_core.tools import ToolException
from pydantic import Field
import pandas as pd
import os
import re
from datetime import datetime
import pydough
from pydough.unqualified import transform_cell
import traceback
from contextlib import redirect_stdout, redirect_stderr
import io

TOP_QUERY_RESULTS = 3

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

class BaselineExecutionTool:
    """Tool for executing PyDough code and returning results."""
    
    name: str = "base_executor"
    description: str = """Executes PyDough code and returns the results as a pandas DataFrame.
    Input should be a Python code block containing PyDough operations.
    The code will be executed in a PyDough environment with access to the TPCH database."""
    
    def __init__(self, db_path: str, metadata_path: str, graph_name: Optional[str] = None):
        """Initialize the PyDough execution tool with database paths.
        
        Args:
            db_path: Path to the SQLite database file.
            metadata_path: Path to the metadata graph JSON file.
            graph_name: Name of the graph inside the metadata. If ``None`` we will
                attempt to infer it from the *metadata_path* filename (expects the
                conventional ``<graph_name>_graph.json`` pattern).  Falling back to
                ``"TPCH"`` maintains backwards-compatibility with existing
                behaviour.
        """
        self.db_path = db_path
        self.metadata_path = metadata_path
        
        # Derive graph name when not explicitly provided
        if graph_name is None:
            base_name = os.path.basename(metadata_path)
            if base_name.endswith("_graph.json"):
                graph_name = base_name.replace("_graph.json", "")
            else:
                graph_name = "TPCH"
        self.graph_name = graph_name
        
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
        
        # Load metadata and connect to database using the *correct* graph name
        pydough.active_session.load_metadata_graph(metadata_path, self.graph_name)
        pydough.active_session.connect_database("sqlite", database=db_path, check_same_thread=False)
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code using the shared helper."""
        return _extract_code_from_text(response)
    
    def _execute_code(self, code: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Execute PyDough code and return the result."""
        try:
            # Create local environment
            local_env = {
                "pydough": pydough,
                "datetime": datetime
            }
            
            # Create string buffers for stdout and stderr
            stdout_buf = io.StringIO()
            stderr_buf = io.StringIO()
            
            # Transform and execute the code with output redirection
            transformed_source = transform_cell(code, "pydough.active_session.metadata", set(local_env))
            
            try:
                with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                    exec(transformed_source, {}, local_env)
            except Exception as e:
                # Get any output that was printed before the error
                output = stdout_buf.getvalue()
                error_output = stderr_buf.getvalue()
                tb = traceback.format_exc()
                
                # Combine all error information
                error_msg = f"Error executing PyDough code:\n"
                if output:
                    error_msg += f"Output before error:\n{output}\n"
                if error_output:
                    error_msg += f"Error output:\n{error_output}\n"
                error_msg += f"Traceback:\n{tb}"
                return None, error_msg
            
            # Get the last variable assigned
            last_variable = list(local_env.values())[-1]
            
            # Convert to DataFrame and then to JSON string
            result_df = pydough.to_df(last_variable)
            if isinstance(result_df, pd.DataFrame):
                result_json = result_df.to_json(orient='records')
                return result_json, None
            else:
                # If not a DataFrame, convert to string
                return str(result_df), None
            
        except Exception as e:
            return None, f"Error in PyDough execution: {str(e)}\nTraceback:\n{traceback.format_exc()}"
    
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
        
        return {
            "dataframe": result,
            "code": extracted_code
        }
    
    async def _arun(self, code: str) -> Dict[str, Any]:
        """Asynchronous version of _run."""
        return self._run(code)

class PyDoughExecutionTool(BaseTool):
    """Tool for executing PyDough code and returning results."""
    
    name: str = "pydough_executor"
    description: str = """Executes PyDough code and returns the results as a pandas DataFrame.
    Input should be a Python code block containing PyDough operations.
    The code will be executed in a PyDough environment with access to the TPCH database."""
    
    db_path: str = Field(..., description="Path to the SQLite database file")
    metadata_path: str = Field(..., description="Path to the metadata graph JSON file")
    graph_name: str = Field("TPCH", description="Name of the graph to load from metadata")
    
    def __init__(self, db_path: str, metadata_path: str, graph_name: str = "TPCH"):
        """Initialize the PyDough execution tool with database paths."""
        super().__init__(db_path=db_path, metadata_path=metadata_path, graph_name=graph_name)
        
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
        pydough.active_session.load_metadata_graph(metadata_path, self.graph_name)
        pydough.active_session.connect_database("sqlite", database=db_path, check_same_thread=False)
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code using the shared helper."""
        return _extract_code_from_text(response)
    
    def _execute_code(self, code: str) -> Tuple[Optional[str], Optional[str]]:
        """Execute PyDough code and return the result."""
        try:
            # Create local environment
            local_env = {
                "pydough": pydough,
                "datetime": datetime
            }
            
            # Create string buffers for stdout and stderr
            stdout_buf = io.StringIO()
            stderr_buf = io.StringIO()
            
            # Transform and execute the code with output redirection
            transformed_source = transform_cell(code, "pydough.active_session.metadata", set(local_env))
            
            try:
                with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                    exec(transformed_source, {}, local_env)
            except Exception as e:
                # Get any output that was printed before the error
                output = stdout_buf.getvalue()
                error_output = stderr_buf.getvalue()
                tb = traceback.format_exc()
                
                # Combine all error information
                error_msg = f"Error executing PyDough code:\n"
                if output:
                    error_msg += f"Output before error:\n{output}\n"
                if error_output:
                    error_msg += f"Error output:\n{error_output}\n"
                error_msg += f"Traceback:\n{tb}"
                return None, error_msg
            
            # Get the last variable assigned
            last_variable = list(local_env.values())[-1]
            
            # Convert to DataFrame and then to JSON string
            result_df = pydough.to_df(last_variable)
            if isinstance(result_df, pd.DataFrame):
                result_json = result_df.head(TOP_QUERY_RESULTS).to_json(orient='records')
                return result_json, None
            else:
                # If not a DataFrame, convert to string
                return str(result_df), None
            
        except Exception as e:
            return None, f"Error in PyDough execution: {str(e)}\nTraceback:\n{traceback.format_exc()}"
    
    def _run(self, input: str) -> str:
        """Execute the PyDough code and return the results."""
        # Extract code from the input.  We purposefully *do not* require fenced
        # blocks so that the tool can execute even if the LLM forgets them.
        code = self._extract_code(input)
        if not code:
            raise ToolException(
                "No PyDough code found in the tool input. Make sure to provide valid code to execute."
            )

        try:
            result_json, err = self._execute_code(code)
            if err:
                raise ToolException(err)
            return result_json
        except Exception as e:
            raise ToolException(f"{type(e).__name__}: {e}")
    
    async def _arun(self, input: str) -> str:
        """Asynchronous version of _run."""
        return self._run(input)
    
# ---------------------------------------------------------------------------
# Shared helper utilities
# ---------------------------------------------------------------------------

def _extract_code_from_text(text: str) -> str:
    """Best-effort extraction of a Python snippet from *text*.

    The LLM sometimes forgets to wrap code in fenced blocks or adds prefixes
    such as "Action Input:" when working in a ReAct loop.  To make the
    execution tools more resilient we:

    1. Look for a fenced code block – ```python ... ``` or ``` ... ``` – and
       return its content if found.
    2. Otherwise, strip a leading "Action Input:" (case-insensitive) label and
       treat the remainder of the string as raw code.

    If nothing that looks like code can be recovered we return the empty
    string so that the caller may decide how to handle the situation.
    """

    if not isinstance(text, str):
        return ""

    # 1. Look for fenced blocks (with or without explicit language spec)
    fenced_match = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fenced_match:
        return fenced_match.group(1).strip()

    # 2. Fallback – remove common prefixes like "Action Input:" and treat the
    #    whole remainder as code.
    cleaned = re.sub(r"^\s*Action Input:\s*", "", text, flags=re.IGNORECASE).strip()
    return cleaned
    