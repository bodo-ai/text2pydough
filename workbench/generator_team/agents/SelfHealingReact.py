from __future__ import annotations

"""Self-healing ReAct SQL agent.

This module is a *drop-in* extension of the existing `ReAct.py` agent that
adds the self-healing generate-check-run loop described in the LangGraph SQL
agent tutorial:
https://langchain-ai.github.io/langgraph/tutorials/sql-agent/#3-customizing-the-agent

The agent is compiled as a LangGraph and exposes a single `ask` method for
end-to-end Q&A over a SQLite database.  The graph executes the following
steps until the query succeeds, or the model decides no further tool calls
are necessary:

1. ``sql_db_list_tables``  – enumerate tables
2. ``sql_db_schema``       – fetch schemas for the relevant tables
3. ``generate_query``      – LLM decides on the SQL to run (ReAct)
4. ``sql_db_query_checker``– validate the query using the checker tool
5. ``sql_db_query``        – run the query and return the results

If the checker or the database returns an error, control flows back to
``generate_query`` so the model can iterate.
"""

from typing import List, Dict, Union, TypedDict
import os
import sys
from pathlib import Path

# Also capture the package directory itself so that submodules like
# ``pydough_data`` (which live *inside* ``generator_team``) can be imported
# with a top-level statement: ``import pydough_data``.  Some existing code
# relies on that shortcut.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_GENERATOR_PKG_DIR = _PROJECT_ROOT / "generator_team"

for _p in (str(_PROJECT_ROOT), str(_GENERATOR_PKG_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    BaseMessage,
)
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.prebuilt import create_react_agent  # type: ignore
from langgraph.graph import StateGraph, END, START, MessagesState

# Re-use the LLM factory & constants from the sibling ReAct agent ----------------
from generator_team.agents.ReAct import create_llm, GCP_MODELS, TEMPERATURE, TOP_P  # type: ignore

###############################################################################
# Graph state definition                                                       #
###############################################################################

# Extend the graph state so we can track execution errors and iteration count.
# This enables conditional routing and a deterministic stop condition.

class AgentState(TypedDict):
    """LangGraph node/edge state for the SQL agent."""

    messages: List[BaseMessage]
    error: bool  # True if the last DB execution failed
    step: int  # How many times we have attempted to run a query

###############################################################################
# Self-healing SQL agent                                                       #
###############################################################################

class SelfHealingSQLAgent:
    """End-to-end SQL Q&A agent with automatic query fixing."""

    def __init__(
        self,
        db_path: str,
        model_name: str | None = None,
        temperature: float = TEMPERATURE,
        top_p: float = TOP_P,
        top_k: int = 5,
        max_steps: int = 10,
    ) -> None:
        # ------------------------------------------------------------------ LLM
        if model_name is None:
            model_name = GCP_MODELS[0]
        self.llm = create_llm(model_name, temperature=temperature, top_p=top_p)

        # ------------------------------------------------------------ SQL tools
        db_uri = f"sqlite:///{os.path.abspath(db_path)}"
        self.db = SQLDatabase.from_uri(db_uri)
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.tools = {t.name: t for t in self.toolkit.get_tools()}

        # ---------------------------------------------------------------- Prompts
        # Read the prompt templates from Markdown files so that non-coders can
        # edit them without touching the Python source.  Fallback to the baked-
        # in strings if the files are missing.

        prompt_dir = os.path.join(os.path.dirname(__file__), "pydough_data", "prompts")

        def _load_prompt(filename: str, default: str) -> str:
            path = os.path.join(prompt_dir, filename)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            return default

        gen_default = (
            """
            You are an agent designed to interact with a SQL database. Given an
            input question, create a syntactically correct {dialect} query to
            run, then look at the results of the query and return the answer.
            Unless the user specifies a specific number of examples to obtain,
            always limit your query to at most {top_k} rows.

            You can order the results by a relevant column to return the most
            interesting examples in the database. Never query for all the
            columns from a specific table – only ask for the relevant columns
            given the question.

            DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.)
            to the database.
            
            IMPORTANT: You MUST use the sql_db_query_checker tool to validate
            your query before execution. Always call sql_db_query_checker first
            with your proposed SQL query.
            """
        )

        check_default = (
            """
            You are a SQL expert with a strong attention to detail. Double-check
            the {dialect} query for common mistakes, including:
            - Using NOT IN with NULL values
            - Using UNION when UNION ALL should have been used
            - Using BETWEEN for exclusive ranges
            - Data type mismatch in predicates
            - Properly quoting identifiers
            - Using the correct number of arguments for functions
            - Casting to the correct data type
            - Using the proper columns for joins

            If there are any of the above mistakes, rewrite the query. If there
            are no mistakes, just reproduce the original query.

            You MUST call the sql_db_query tool to execute the query after
            running this check. Always use sql_db_query to run the final query.
            """
        )

        self._generate_query_system_prompt = _load_prompt(
            "sql_generate_query_prompt.md", gen_default
        ).format(dialect=self.db.dialect, top_k=top_k).strip()

        self._check_query_system_prompt = _load_prompt(
            "sql_check_query_prompt.md", check_default
        ).format(dialect=self.db.dialect).strip()

        # ----------------------------------------------------- LangGraph build
        self.graph = self._build_graph(top_k, max_steps=max_steps)

        # Store for reference
        self._max_steps = max_steps

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _wrap_tool(tool):
        """Wrap a LangChain ``BaseTool`` for use in a LangGraph state."""

        def _node(state: AgentState) -> AgentState:  # type: ignore[override]
            last_user_msg = state["messages"][-1].content if state["messages"] else ""
            result = tool.invoke(last_user_msg)  # tools expect ``str`` input
            state["messages"].append(AIMessage(content=str(result)))
            return state

        return _node

    # ----------------------------------------------------------------- graph
    def _build_graph(self, top_k: int, max_steps: int = 10):
        list_tables_node = self._wrap_tool(self.tools["sql_db_list_tables"])
        
        # Create a separate node for calling get_schema tool
        def call_get_schema(state: AgentState) -> AgentState:
            """Call the schema tool for relevant tables."""
            # Get the table list from the previous message
            tables_msg = state["messages"][-1].content
            
            # Use the schema tool to get relevant table schemas
            # For now, we'll use a simple heuristic to select tables
            # In a more sophisticated implementation, you could use an LLM to decide
            available_tables = self.db.get_usable_table_names()
            
            # Take first few tables as relevant (this could be improved with LLM selection)
            relevant_tables = ", ".join(available_tables[:3])  # Simple heuristic
            
            result = self.tools["sql_db_schema"].invoke(relevant_tables)
            state["messages"].append(AIMessage(content=str(result)))
            return state

        # ------------------------- generate_query (LLM + tools) -------------
        def generate_query(state: AgentState) -> AgentState:
            """Generate a SQL query using the query checker tool."""
            # Bump the iteration counter *before* doing any further work so that
            # attempts that fail during validation (i.e. never reach run_query)
            # are still counted towards the overall `max_steps` limit.
            state["step"] += 1

            # Hard stop safeguard – return immediately once we exceed the limit
            if state["step"] > max_steps:
                return state  # will be routed to END by should_continue/after_run

            system_msg = SystemMessage(content=self._generate_query_system_prompt)

            # Always use the query checker tool first - this is the key fix
            llm_with_tools = self.llm.bind_tools(
                [self.tools["sql_db_query_checker"]],
                tool_choice="sql_db_query_checker"  # Force using the checker
            )

            response = llm_with_tools.invoke([system_msg] + state["messages"])
            return {**state, "messages": state["messages"] + [response]}

        # ------------------------- check_query (LLM validation) -------------
        def check_query(state: AgentState) -> AgentState:
            """Validate and potentially fix the SQL query."""
            # Extract the SQL text from the previous tool-call
            last_msg = state["messages"][-1]
            tool_call = last_msg.tool_calls[0]
            query_text = tool_call["args"]["query"]

            system_msg = SystemMessage(content=self._check_query_system_prompt)
            user_msg = HumanMessage(content=query_text)

            # The checker must call sql_db_query after validation
            llm_with_tools = self.llm.bind_tools(
                [self.tools["sql_db_query"]], 
                tool_choice="sql_db_query"  # Force execution after check
            )
            response = llm_with_tools.invoke([system_msg, user_msg])

            return {**state, "messages": state["messages"] + [response]}

        # ------------------------- routing logic ----------------------------
        def should_continue(state: AgentState) -> str:
            """Route based on the last tool call."""
            # Abort only *after* we exceed the configured limit so that the
            # N-th generate→run cycle is allowed to complete.  We perform the
            # stricter ``>=`` check in ``after_run_query`` once the execution
            # attempt has finished.
            if state["step"] > max_steps:
                return END

            last = state["messages"][-1]
            if last.tool_calls:
                name = last.tool_calls[0]["name"]
                if name == "sql_db_query_checker":
                    return "check_query"  # Fixed: checker goes to check_query
                elif name == "sql_db_query":
                    return "run_query"    # Fixed: query goes to run_query
            return END

        # ------------------------- assemble LangGraph -----------------------
        builder = StateGraph(AgentState)

        builder.add_node("list_tables", list_tables_node)
        builder.add_node("call_get_schema", call_get_schema)  # Separate node
        builder.add_node("generate_query", generate_query)
        builder.add_node("check_query", check_query)

        # -------------------- run_query node (with error handling) --------
        def run_query_node(state: AgentState) -> AgentState:
            """Execute the SQL query & capture success / failure."""
            # Extract SQL text from the tool call produced by the checker
            last_msg = state["messages"][-1]
            sql_query: str | None = None
            if getattr(last_msg, "tool_calls", None):
                try:
                    sql_query = last_msg.tool_calls[0]["args"]["query"]
                except Exception:
                    sql_query = None

            # Fall back to raw content if parsing fails (defensive).
            query_input = sql_query or last_msg.content or ""

            try:
                result = self.tools["sql_db_query"].invoke(query_input)
                # Check if result is empty or indicates an error
                if result is None or (isinstance(result, str) and ("error" in result.lower() or len(result.strip()) == 0)):
                    state["error"] = True
                elif isinstance(result, (list, tuple)) and len(result) == 0:
                    state["error"] = True
                else:
                    state["error"] = False
                    
                state["messages"].append(AIMessage(content=str(result)))
            except Exception as e:
                state["messages"].append(AIMessage(content=f"[error] {e}"))
                state["error"] = True

            # NOTE: We no longer increment the step counter here because it
            # is already bumped in ``generate_query`` at the *start* of each
            # self-healing attempt.  Incrementing here as well caused the
            # counter to advance twice per attempt, prematurely exhausting
            # the max_steps budget.

            return state

        builder.add_node("run_query", run_query_node)

        # Fixed edge connections to match tutorial pattern
        builder.add_edge(START, "list_tables")
        builder.add_edge("list_tables", "call_get_schema")  # Fixed: separate schema node
        builder.add_edge("call_get_schema", "generate_query")  # Fixed: schema to generate
        builder.add_conditional_edges("generate_query", should_continue)
        builder.add_edge("check_query", "run_query")

        # After executing the query, decide whether to self-heal or finish.
        def after_run_query(state: AgentState) -> str:
            # Stop if the query succeeded or we hit the max retry limit.
            if not state["error"] or state["step"] >= max_steps:
                return END
            return "generate_query"  # Loop back to generate_query for self-healing

        builder.add_conditional_edges("run_query", after_run_query)

        return builder.compile()

    # ---------------------------------------------------------------- public
    def ask(self, question: str) -> Dict[str, Union[str, List]]:
        """Run the full self-healing pipeline for *question* and return the
        LangGraph output (messages, etc.)."""
        initial_state: AgentState = {
            "messages": [HumanMessage(content=question)],
            "error": False,
            "step": 0,
        }
        # Provide a recursion_limit to LangGraph so that *internal* safeguards
        # align with our own max_steps configuration (adds a small buffer).
        recursion_limit = max(25, self._max_steps * 3)
        return self.graph.invoke(initial_state, config={"recursion_limit": recursion_limit})  # type: ignore[arg-type]

if __name__ == "__main__":
    """Quick smoke-test for the self-healing SQL agent.

    Run a couple of sample questions against the TPCH SQLite database so that
    users can see the agent in action and verify everything is wired up
    correctly.  Environment variables allow the DB path and experiment name to
    be overridden without editing the source.
    """

    # ---------------------------------------------------------------- observability backends (MLflow ↔ Phoenix)
    # Decide whether to report traces to MLflow or Phoenix.  This mirrors
    # the implementation in ``gradio_server.py`` so that a single set of
    # environment variables can control observability across the whole code-
    # base.
    try:
        from openinference.instrumentation.langchain import LangChainInstrumentor  # type: ignore
        LangChainInstrumentor().instrument()
    except Exception as e:  # pragma: no cover – instrumentation is optional
        print("[warn] LangChain instrumentation failed:", e)

    USE_MLFLOW = os.getenv("USE_MLFLOW", "false").lower() in ("1", "true", "yes")

    if USE_MLFLOW:
        try:
            import mlflow  # type: ignore

            MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            mlflow.set_experiment(os.getenv("EXPERIMENT_NAME", "self-healing-sql-agent"))

            # Enable automatic LangChain tracing via MLflow
            mlflow.langchain.autolog(
                log_traces=True,
                log_models=True,
                log_input_examples=True,
                log_model_signatures=True,
                registered_model_name="self_healing_sql_agent",
            )
        except Exception as e:  # pragma: no cover – MLflow is optional
            print("[warn] MLflow tracing disabled:", e)
    else:
        try:
            from phoenix.otel import register  # type: ignore

            API_KEY = os.getenv("PHOENIX_API_KEY")
            COLLECTOR_ENDPOINT = os.getenv("PHOENIX_COLLECTOR_ENDPOINT")

            register(
                endpoint=COLLECTOR_ENDPOINT,
                headers={"Authorization": f"Bearer {API_KEY}"},
                project_name=os.getenv("EXPERIMENT_NAME", "self-healing-sql-agent"),
                auto_instrument=True,
                protocol="http/protobuf",  # force HTTP transport to match gradio_server.py
            )
        except Exception as e:  # pragma: no cover – Phoenix is optional
            print("[warn] Phoenix tracing disabled:", e)

    # ---------------------------------------------------------------- params
    # Resolve the TPCH demo database relative to the *repository* root so the
    # script works on Windows, macOS and Linux/WSL without modification.
    # ``_PROJECT_ROOT`` is defined at the top of the file and already points
    # to the root of the git workspace.
    default_db = (_PROJECT_ROOT / "TPCH" / "test_data" / "tpch.db").resolve()
    db_path = Path(os.getenv("DB_PATH", str(default_db))).expanduser()

    if not db_path.exists():
        raise FileNotFoundError(f"SQLite database not found at: {db_path}")

    # Instantiate the agent ---------------------------------------------------
    print("\nInitialising Self-healing SQL agent…")
    demo_agent = SelfHealingSQLAgent(db_path=str(db_path))

    # Sample questions to demonstrate functionality --------------------------
    sample_questions = [
        "How many orders are recorded in the ORDERS table?",
        "List the top 5 customers by their total account balance.",
    ]

    for q in sample_questions:
        print("\n" + "=" * 80)
        print("Question:", q)
        print("-" * 80)
        try:
            result = demo_agent.ask(q)
            # Pretty-print the final assistant message for readability
            final_msg = result["messages"][-1].content if result.get("messages") else "[No messages]"
            print("Assistant reply:\n", final_msg)
            # If the DB tool returned tabular data, it will be captured as a string
            # inside the assistant reply; no further handling needed here.
        except Exception as err:
            print("[error]", err)
    print("\nDemo finished – everything looks good if no errors were raised!\n")

__all__ = ["SelfHealingSQLAgent"] 