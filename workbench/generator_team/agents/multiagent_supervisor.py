from __future__ import annotations

"""Multi-agent Supervisor framework ⚙️

This module provides a **single public helper** – :func:`create_supervisor_app` –
that turns a list of markdown prompt templates into a fully-wired **Supervisor →
N workers** LangGraph application.

Key design goals
----------------
1. **Modularity** –  add/remove agents by simply editing the *TEMPLATES* list or
   passing a different list to :func:`create_supervisor_app`.
2. **Convention over configuration** –  every worker prompt lives in
   `pydough_data/prompts/<agent_name>.md`.  The *file name* becomes the
   run-time *agent.name*.
3. **Re-use existing tooling** –  each worker is a LangGraph `ReAct` agent so
   that it can call tools just like the rest of the codebase (see
   :pymod:`generator_team.agents.ReAct`).
4. **Minimal ceremony** – sensible defaults for model, temperature, etc. are
   inherited from the existing `ReAct` module.

Example
~~~~~~~
>>> from generator_team.agents.multiagent_supervisor import create_supervisor_app
>>> app = create_supervisor_app()   # 2 default agents – information_extractor / query_generator
>>> result = app.invoke({"messages": [{"role": "user", "content": "list all tables"}]})
>>> print(result["messages"][-1].content)
"""

from pathlib import Path
from typing import List, Literal, Annotated
import sys
import os

from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.types import Command, Send

from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import HumanMessage
from langchain_core.tools import Tool
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# 🛣️  Path setup – ensure the *repository* root & `generator_team` package ----
# are on `sys.path` so that absolute imports work when running this file
# directly (e.g. `python multiagent_supervisor.py`).
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_GENERATOR_PKG_DIR = _PROJECT_ROOT / "generator_team"

# Load environment variables early so that downstream config picks them up.
load_dotenv()

for _p in (str(_PROJECT_ROOT), str(_GENERATOR_PKG_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# ✅ Default configuration values – tweak here or override at call-time
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # <project>/generator_team
PROMPTS_DIR = BASE_DIR / "pydough_data" / "prompts"

# Default to Gemini 2.5-flash preview (readily available on Vertex AI)
DEFAULT_MODEL = "gemini-2.5-flash-preview-05-20"  # can still be overridden at runtime
DEFAULT_DB_PATH = "C:/Users/david/bodo/TPCH/test_data/tpch.db"
DEFAULT_METADATA_PATH = "C:/Users/david/bodo/TPCH/test_data/tpch_demo_graph.json"

# When no explicit workers are supplied, we fall back to **two**
# `PydoughGeneratorAgent` instances – one acting as an *information extractor*
# and another as a *query generator*.
DEFAULT_AGENT_TEMPLATES = [  # still available for template-only setups
    "information_extractor",
    "query_generator",
]

# ---------------------------------------------------------------------------
# 🛤️  Path utility – convert Windows paths when running under Linux/WSL -------
# ---------------------------------------------------------------------------

def _convert_windows_to_wsl_path(windows_path: str) -> str:
    """Return a WSL-compatible path when given a Windows absolute path.

    No-op when the input is already POSIX-style or when executing on Windows.
    """
    if os.name == "nt":  # Running on native Windows → nothing to do
        return windows_path

    # Detect a Windows drive pattern like "C:\path" or "C:/path"
    if ":" in windows_path and windows_path[1:3] in (":/", ":\\"):
        drive, path_rest = windows_path.split(":", 1)
        drive = drive.lower()
        path_rest = path_rest.replace("\\", "/")  # normalise slashes
        return f"/mnt/{drive}{path_rest}"

    return windows_path

# ---------------------------------------------------------------------------
# 🛠️  Helper – build a single ReAct worker from a markdown prompt -------------
# ---------------------------------------------------------------------------

def _build_worker_agent(template_name: str, *, model: str = DEFAULT_MODEL):
    """Create a LangGraph **ReAct** agent from `<PROMPTS_DIR>/<name>.md`."""
    from langchain_google_vertexai import ChatVertexAI  # use same provider as ReAct

    # 1. Agent-specific **task** prompt (required)
    task_path = PROMPTS_DIR / f"{template_name}.md"
    if not task_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {task_path}")

    task_txt = task_path.read_text(encoding="utf-8")

    # 2. System prompt – search for `<name>_system_prompt.md`, else generic.
    specific_sys_path = PROMPTS_DIR / f"{template_name}_system_prompt.md"
    generic_sys_path = PROMPTS_DIR / "system_prompt.md"

    if specific_sys_path.exists():
        system_txt = specific_sys_path.read_text(encoding="utf-8")
    else:
        system_txt = generic_sys_path.read_text(encoding="utf-8") if generic_sys_path.exists() else ""

    combined_prompt = system_txt + "\n\n" + task_txt if system_txt else task_txt

    # Limit Gemini to *one* function-call per assistant turn to satisfy the
    # strict <function_call> ⇄ <function_response> matching enforced by the
    # Vertex AI API (otherwise we risk the "number of function response parts
    # is not equal to the number of function call parts" 400 error).
    llm = ChatVertexAI(
        model=model,
        temperature=0,
        # See: https://cloud.google.com/vertex-ai/docs/generative-ai/function-calling#python
        # The *tool_config* map is passed straight through as-is to the
        # `generateContent` request, so we bundle it under `model_kwargs`.
        model_kwargs={
            "tool_config": {
                "function_calling_config": {
                    "mode": "AUTO",  # allow the model to decide *if* it should call
                    "max_consecutive_function_calls": 1,  # …but never more than one!
                }
            }
        },
    )

    agent = create_react_agent(
        model=llm,
        tools=[],
        prompt=combined_prompt,
        name=template_name,
    )
    return agent

# ---------------------------------------------------------------------------
# 🛠️  Helper – create a hand-off tool allowing the supervisor LLM to jump -----
# ---------------------------------------------------------------------------

def _create_handoff_tool(agent_name: str):
    """Return a *tool* that, when called, transfers execution to *agent_name*."""

    tool_name = f"transfer_to_{agent_name}"
    description = f"Delegate the current task to `{agent_name}`."

    def _handoff(
        tool_input: object | None = None,  # <- captures any LLM-supplied input (ignored)
        tool_call_id: Annotated[str, InjectedToolCallId] | None = None,
        **extra_args,
    ) -> Command:
        """LangChain tool that routes execution to *agent_name*."""

        # Simply hand back control to the *parent* graph (the Supervisor
        # workflow) **without** overriding the `messages` list.  LangGraph
        # will automatically append the tool-response message whose content is
        # whatever this function returns (here we choose an empty JSON
        # object).  Crucially, by not touching `state["messages"]` we preserve
        # the *assistant* function-call that triggered the tool, keeping the
        # counts balanced for Gemini.

        return Command(
            goto=agent_name,
            graph=Command.PARENT,
        )

    # Create a Tool object from the Python function – avoids version-specific
    # kwargs issues with the @tool decorator.
    return Tool.from_function(_handoff, name=tool_name, description=description)

# ---------------------------------------------------------------------------
# 🧠  Build the supervisor ReAct agent ---------------------------------------
# ---------------------------------------------------------------------------

def _build_supervisor_agent(worker_names: List[str], *, model: str = DEFAULT_MODEL):
    """Supervisor with *handoff tools* to each worker."""
    from langchain_google_vertexai import ChatVertexAI

    tools = [_create_handoff_tool(w) for w in worker_names]
    # Same single-call safeguard for **worker** ReAct agents (each SQL/utility
    # tool invocation must be followed by exactly one response part).
    llm = ChatVertexAI(
        model=model,
        temperature=0,
        model_kwargs={
            "tool_config": {
                "function_calling_config": {
                    "mode": "AUTO",
                    "max_consecutive_function_calls": 1,
                }
            }
        },
    )

    # ------------------------------------------------------------------
    # 📄  Supervisor prompt resolution: prefer *file* → generic → fallback
    # ------------------------------------------------------------------

    # 1️⃣  Always build a dynamic helper string listing available workers – we may
    #     inject this into a template or use it directly for the fallback prompt.
    worker_lines = "\n".join(
        f"- `{name}` – use for tasks described in the `{name}` prompt." for name in worker_names
    )

    # 2️⃣  Check for an explicit supervisor system prompt file.
    specific_sup_path = PROMPTS_DIR / "supervisor_system_prompt.md"
    generic_sys_path = PROMPTS_DIR / "system_prompt.md"

    if specific_sup_path.exists():
        # Read the custom prompt and allow optional `{worker_lines}` placeholder replacement
        raw_txt = specific_sup_path.read_text(encoding="utf-8")
        sup_prompt = raw_txt.replace("{worker_lines}", worker_lines)
    elif generic_sys_path.exists():
        # Fall back to the repo-wide generic system prompt if present.
        generic_txt = generic_sys_path.read_text(encoding="utf-8")
        sup_prompt = generic_txt.replace("{worker_lines}", worker_lines)
    else:
        # Ultimate fallback – use the hard-coded string that existed before.
        sup_prompt = (
            "You are a supervisor agent.  Your job is to decide *which* specialised\n"
            f"agent should do the next step.  Available agents:\n{worker_lines}\n\n"
            "Use exactly **one** `transfer_to_*` tool at a time.  Never perform the\n"
            "task yourself.  When the overall goal is met, respond directly to the\n"
            "user without calling any tool."
        )

    supervisor = create_react_agent(
        model=llm,
        tools=tools,
        prompt=sup_prompt,
        name="supervisor",
    )
    return supervisor

# ---------------------------------------------------------------------------
# 🏗️  Optional – build a worker around **PydoughGeneratorAgent** -------------
# ---------------------------------------------------------------------------

def _build_pydough_worker(name: str,
                          *,
                          db_path: str = DEFAULT_DB_PATH,
                          metadata_path: str = DEFAULT_METADATA_PATH,
                          **agent_kwargs):
    """Wrap :class:`PydoughGeneratorAgent` so it can live inside LangGraph."""

    from langchain_core.messages import AIMessage
    from generator_team.agents.ReAct import PydoughGeneratorAgent  # local import

    # choose system prompt file if exists
    specific_sys_path = PROMPTS_DIR / f"{name}_system_prompt.md"
    system_path = specific_sys_path if specific_sys_path.exists() else PROMPTS_DIR / "system_prompt.md"

    # ------------------------------------------------------------------
    # 🔌   Build SQL database tools (list tables / schema / query / checker)
    # ------------------------------------------------------------------
    try:
        from langchain_community.utilities import SQLDatabase  # local import
        from langchain_community.agent_toolkits import SQLDatabaseToolkit
        from generator_team.agents.ReAct import create_llm, TEMPERATURE, TOP_P  # avoid circular import issues

        # 1. Create a lightweight LLM instance for tool internal reasoning.
        llm_for_tools = create_llm(DEFAULT_MODEL, temperature=TEMPERATURE, top_p=TOP_P)

        # 2. Connect to the SQLite database the worker will operate on.
        real_db_path = os.path.abspath(_convert_windows_to_wsl_path(db_path))
        db_uri = f"sqlite:///{real_db_path}"
        sql_db = SQLDatabase.from_uri(db_uri)

        # 3. Generate the full set of SQL tools (list_tables, schema, query, checker).
        sql_toolkit = SQLDatabaseToolkit(db=sql_db, llm=llm_for_tools)
        sql_tools = sql_toolkit.get_tools()
    except Exception as e:
        # In case of any failure (missing deps, invalid DB), fall back gracefully
        print("[warn] Failed to initialise SQL tools for worker", name, "-", e)
        sql_tools = []

    # Ensure PyDough context flags default to False unless explicitly overridden
    agent_kwargs.setdefault("include_schema", False)
    agent_kwargs.setdefault("include_cheatsheet", False)

    # Merge any caller-supplied tools with the SQL toolkit (caller wins if duplicates)
    extra_tools = agent_kwargs.pop("tools", []) if "tools" in agent_kwargs else []
    combined_tools = extra_tools + sql_tools

    pyd_agent = PydoughGeneratorAgent(
        db_path=_convert_windows_to_wsl_path(db_path),
        metadata_path=_convert_windows_to_wsl_path(metadata_path),
        system_prompt_path=str(system_path),
        tools=combined_tools,
        **agent_kwargs,
    )

    def _node(state: MessagesState) -> Command[Literal["supervisor"]]:
        # Identify the most recent *user* message (skip tool/assistant chatter)
        question = None
        for _msg in reversed(state["messages"]):
            if isinstance(_msg, HumanMessage) or getattr(_msg, "role", None) == "user":
                question = _msg.content if hasattr(_msg, "content") else _msg["content"]
                break

        # Fallback: if no user message found, default to the latest entry
        if question is None:
            last_msg = state["messages"][-1]
            question = last_msg.content if hasattr(last_msg, "content") else last_msg["content"]
        
        result = pyd_agent.generate_and_execute(question)
        answer_txt = result.get("answer") or str(result)
        if not isinstance(answer_txt, (str, dict)):
            answer_txt = str(answer_txt)

        return Command(
            goto="supervisor",
            update={
                "messages": state["messages"] + [AIMessage(content=answer_txt, name=name)]
            },
        )

    _node.__name__ = name
    _node.name = name  # so LangGraph uses this as the node identifier
    return _node

# ---------------------------------------------------------------------------
# 🏗️  Optional – build a worker around **SelfHealingSQLAgent** -------------
# ---------------------------------------------------------------------------

def _build_selfhealing_worker(
    name: str,
    *,
    db_path: str = DEFAULT_DB_PATH,
    **agent_kwargs,
):
    """Wrap :class:`SelfHealingSQLAgent` so it can live inside LangGraph."""

    from langchain_core.messages import AIMessage
    from generator_team.agents.SelfHealingReact import SelfHealingSQLAgent  # local import

    # Instantiate the self-healing SQL agent – it manages its own prompt/tooling.
    sh_agent = SelfHealingSQLAgent(db_path=_convert_windows_to_wsl_path(db_path), **agent_kwargs)

    def _node(state: MessagesState) -> Command[Literal["supervisor"]]:
        # Identify the most recent *user* message (skip tool/assistant chatter)
        question = None
        for _msg in reversed(state["messages"]):
            if isinstance(_msg, HumanMessage) or getattr(_msg, "role", None) == "user":
                question = _msg.content if hasattr(_msg, "content") else _msg["content"]
                break

        # Fallback: if no user message found, default to the latest entry
        if question is None:
            last_msg = state["messages"][-1]
            question = last_msg.content if hasattr(last_msg, "content") else last_msg["content"]

        result = sh_agent.ask(question)
        # Extract the assistant's reply (last message of the LangGraph output)
        answer_txt = (
            result["messages"][-1].content
            if result and result.get("messages")
            else str(result)
        )
        # Ensure the message content is a supported type (str or dict)
        if not isinstance(answer_txt, (str, dict)):
            answer_txt = str(answer_txt)

        return Command(
            goto="supervisor",
            update={
                "messages": state["messages"] + [AIMessage(content=answer_txt, name=name)]
            },
        )

    _node.__name__ = name
    _node.name = name  # so LangGraph uses this as the node identifier
    return _node

# ---------------------------------------------------------------------------
# 🌐  Public API – create the Supervisor ⇢ Workers LangGraph ------------------
# ---------------------------------------------------------------------------

def create_supervisor_app(
    *,
    template_names: List[str] | None = None,
    worker_agents: List | None = None,
    model: str = DEFAULT_MODEL,
    db_path: str | None = None,
    metadata_path: str | None = None,
    pydough_agent_kwargs: dict | None = None,
    use_selfhealing_query_generator: bool = False,
):
    """Return a compiled LangGraph *application* implementing Supervisor → N workers.

    Parameters
    ----------
    template_names
        List of prompt file basenames (without .md).  When *None*, falls back
        to :pydata:`DEFAULT_AGENT_TEMPLATES`.
    worker_agents
        List of pre-built worker agents.  When *None*, falls back to
        :pydata:`template_names`.
    model
        Model passed to *all* agents (workers + supervisor).  Override as
        needed, e.g. "gpt-4o".
    db_path
        Path to the SQLite database for the worker.  When *None*, falls back to
        the environment variable `DB_PATH`, or defaults to `C:/Users/david/bodo/TPCH/test_data/tpch.db`.
    metadata_path
        Path to the metadata JSON file for the worker.  When *None*, falls back to
        the environment variable `METADATA_PATH`, or defaults to `C:/Users/david/bodo/TPCH/test_data/tpch_demo_graph.json`.
    pydough_agent_kwargs
        Additional keyword arguments to pass to :func:`_build_pydough_worker`.
    use_selfhealing_query_generator
        When *True*, build the "query_generator" worker using
        :class:`SelfHealingSQLAgent` instead of the default
        :class:`PydoughGeneratorAgent`.
    """

    # ------------------------------------------------------------------
    # 🔄  Resolve database & metadata paths
    # ------------------------------------------------------------------
    db_path = _convert_windows_to_wsl_path(
        db_path or os.getenv("DB_PATH", str(_PROJECT_ROOT / "TPCH" / "test_data" / "tpch.db"))
    )
    metadata_path = _convert_windows_to_wsl_path(
        metadata_path or os.getenv("METADATA_PATH", str(_PROJECT_ROOT / "TPCH" / "test_data" / "tpch_demo_graph.json"))
    )

    # ------------------------------------------------------------------
    # 🧩  Build or accept workers
    # ------------------------------------------------------------------
    # Branch 1 – caller supplies **pre-built** worker objects -----------------
    if worker_agents is not None:
        workers = {ag.name: ag for ag in worker_agents}
    # Branch 2 – legacy template build path ----------------------------------
    elif template_names is not None:
        workers = {name: _build_worker_agent(name, model=model) for name in template_names}
    # Branch 3 – default = two PydoughGeneratorAgent workers ------------------
    else :
        if pydough_agent_kwargs is None:
            pydough_kwargs = {"include_schema": False, "include_cheatsheet": False}
        else:
            pydough_kwargs = {"include_schema": False, "include_cheatsheet": False, **pydough_agent_kwargs}
        # Optionally swap the query_generator implementation
        if use_selfhealing_query_generator:
            workers = {
                "information_extractor": _build_pydough_worker(
                    "information_extractor",
                    db_path=db_path,
                    metadata_path=metadata_path,
                    **pydough_kwargs,
                ),
                "query_generator": _build_selfhealing_worker(
                    "query_generator",
                    db_path=db_path,
                ),
            }
        else:
            workers = {
                "information_extractor": _build_pydough_worker(
                    "information_extractor",
                    db_path=db_path,
                    metadata_path=metadata_path,
                    **pydough_kwargs,
                ),
                "query_generator": _build_pydough_worker(
                    "query_generator",
                    db_path=db_path,
                    metadata_path=metadata_path,
                    **pydough_kwargs,
                ),
            }

    # 2️⃣  Build supervisor (with hand-off tools for each worker) -------------
    supervisor_agent = _build_supervisor_agent(list(workers.keys()), model=model)

    # 3️⃣  Assemble the multi-agent graph ------------------------------------
    builder = StateGraph(MessagesState)

    # Add supervisor *object* (its `.name` is "supervisor")
    builder.add_node(supervisor_agent, destinations=(*workers.keys(), END))

    # Add workers
    for name, agent in workers.items():
        builder.add_node(agent)
        builder.add_edge(name, "supervisor")

    # Wire start / end
    builder.add_edge(START, "supervisor")

    app = builder.compile(name="multiagent_supervisor")
    return app

# ---------------------------------------------------------------------------
# 🏁  Quick smoke-test (command-line) ----------------------------------------
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """Quick smoke-test for the multi-agent **Supervisor → Workers** graph.

    Run a couple of sample questions against the TPCH SQLite database so that
    users can verify the Supervisor hand-off mechanism and agent wiring work
    end-to-end without touching any other code.
    """

    # ------------------------------------------------------------------
    # Optional: lightweight LangChain ↔ OpenTelemetry instrumentation so
    # traces appear in MLflow / Phoenix when configured via environment
    # variables.  Replicates the pattern in `SelfHealingReact.py`.
    # ------------------------------------------------------------------
    try:
        from openinference.instrumentation.langchain import LangChainInstrumentor  # type: ignore

        LangChainInstrumentor().instrument()
    except Exception as e:  # pragma: no cover – instrumentation is optional
        print("[warn] LangChain instrumentation failed:", e)

    # ------------------------------------------------------------------
    # MLflow ↔ Phoenix routing (environment controlled) -------------------
    # ------------------------------------------------------------------

    # Decide whether to log to MLflow (otherwise default to Phoenix).
    USE_MLFLOW = os.getenv("USE_MLFLOW", "false").lower() in ("1", "true", "yes")

    if USE_MLFLOW:
        try:
            import mlflow  # type: ignore

            MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            mlflow.set_experiment(os.getenv("EXPERIMENT_NAME", "multiagent-supervisor"))

            # Enable automatic LangChain tracing via MLflow
            mlflow.langchain.autolog(
                log_traces=True,
                log_models=True,
                log_input_examples=True,
                log_model_signatures=True,
                registered_model_name="multiagent_supervisor",
            )
        except Exception as e:
            print("[warn] MLflow tracing disabled:", e)
    else:
        try:
            from phoenix.otel import register  # type: ignore

            API_KEY = os.getenv("PHOENIX_API_KEY")
            COLLECTOR_ENDPOINT = os.getenv("PHOENIX_COLLECTOR_ENDPOINT")

            register(
                endpoint=COLLECTOR_ENDPOINT,
                headers={"Authorization": f"Bearer {API_KEY}"},
                project_name=os.getenv("EXPERIMENT_NAME", "multiagent-supervisor"),
                auto_instrument=True,
                protocol="http/protobuf",  # force HTTP transport
            )
        except Exception as e:
            print("[warn] Phoenix tracing disabled:", e)

    # ------------------------------------------------------------------
    # Build the Supervisor application (defaults: 2 Pydough workers) -----
    # ------------------------------------------------------------------
    print("\nInitialising multi-agent Supervisor demo…")
    app = create_supervisor_app()

    # ------------------------------------------------------------------
    # Sample questions to demonstrate functionality ---------------------
    # ------------------------------------------------------------------
    sample_questions = [
        "List all tables in the database.",
        "Show the top 3 customers by their account balance.",
    ]

    for q in sample_questions:
        print("\n" + "=" * 80)
        print("Question:", q)
        print("-" * 80)
        try:
            result = app.invoke({"messages": [HumanMessage(content=q)]})
            # Pretty-print the final assistant message for readability
            final_msg = (
                result["messages"][-1].content if result.get("messages") else "[No messages]"
            )
            print("Assistant reply:\n", final_msg)
        except Exception as err:
            print("[error]", err)
    print("\nDemo finished – everything looks good if no errors were raised!\n")

# Public exports -------------------------------------------------------------
__all__ = ["create_supervisor_app"] 