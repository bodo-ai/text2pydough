# Generator Team – Agent Suite

This repository bundles several LangChain / LangGraph agents that can reason over relational data with the help of Google's Gemini and other LLMs.

## Table&nbsp;of&nbsp;Contents
1. Quick Start
2. Agents
   - PyDough Generator (ReAct)
   - Self-Healing SQL Agent
   - Multi-Agent Supervisor
   - Evaluator Agent
   - Zero-Shot Variant
3. Environment Variables
4. Installation
5. Running the Demos
6. Tracing & Observability
7. Project Layout

## 1. Quick Start
```bash
# create & activate a virtual-env (Windows: .venv\Scripts\activate)
python -m venv .venv && source .venv/bin/activate

# install all required packages
pip install -r requirements.txt

# copy the example environment and tweak as required
cp .env.example generator_team/.env  # optional helper

# launch the self-healing SQL demo
python -m generator_team.agents.SelfHealingReact
```
The script connects to the bundled TPCH demo database (unless you override `DB_PATH`) and runs a couple of sample questions.

## 2. Agents

### 2.1 PyDough Generator (ReAct)
Location: `generator_team/agents/ReAct.py`

Turns natural-language questions into PyDough code, executes it and returns the resulting `pandas.DataFrame`.
```python
from generator_team.agents.ReAct import PydoughGeneratorAgent

agent = PydoughGeneratorAgent(
    db_path="/path/to/tpch.db",
    metadata_path="/path/to/tpch_demo_graph.json",
)
print(agent.generate_and_execute("List all tables")['dataframe'])
```

### 2.2 Self-Healing SQL Agent
Location: `generator_team/agents/SelfHealingReact.py`

Adds a generate-check-run repair loop that keeps refining the SQL until it succeeds or the retry budget is exhausted.
```bash
python -m generator_team.agents.SelfHealingReact
```

### 2.3 Multi-Agent Supervisor
Location: `generator_team/agents/multiagent_supervisor.py`

Orchestrates N specialised workers via LangGraph.  By default two workers are provided:
* `information_extractor` – extracts entities and intent
* `query_generator` – generates PyDough (or self-healing SQL if enabled)

```python
from generator_team.agents.multiagent_supervisor import create_supervisor_app
app = create_supervisor_app()  # 2 default workers
resp = app.invoke({"messages": [{"role": "user", "content": "Show top 3 customers"}]})
print(resp["messages"][-1].content)
```
CLI demo:
```bash
python -m generator_team.agents.multiagent_supervisor
```

### 2.4 Evaluator Agent
Location: `generator_team/agents/evaluator_agent.py`

Evaluates whether a generated answer matches the ground-truth SQL result by combining LLM reasoning with a pre-computed DataFrame comparison.

### 2.5 Zero-Shot Variant
Location: `generator_team/agents/zero_shot_agent.py`

A lighter alternative to the ReAct agent that relies purely on prompt engineering.

## 3. Environment Variables (.env)
```
# LLM
MODEL_ID=gemini-2.5-flash-preview-05-20
TEMPERATURE=0.3

# Database
DB_PATH=/abs/path/to/your.db
METADATA_PATH=/abs/path/to/metadata.json

# Observability
USE_MLFLOW=false
MLFLOW_TRACKING_URI=http://localhost:5000
EXPERIMENT_NAME=agent-playground

# Phoenix (only when USE_MLFLOW=false)
PHOENIX_API_KEY=<your-key>
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006
```
Any variable can be omitted – the agents fall back to sensible defaults.

## 4. Installation
All Python dependencies are listed in `requirements.txt`.  Extra packages for tracing are optional but recommended.

## 5. Running the Demos
```bash
# Self-healing SQL Agent
activate-your-env
python -m generator_team.agents.SelfHealingReact

# Multi-agent Supervisor
python -m generator_team.agents.multiagent_supervisor

# Zero-shot generator
python -m generator_team.agents.zero_shot_agent
```

## 6. Tracing & Observability
Set `USE_MLFLOW=true` and point `MLFLOW_TRACKING_URI` to an MLflow server to automatically capture LangChain / LangGraph traces. When `USE_MLFLOW=false` the code falls back to [Phoenix](https://github.com/BerriAI/phoenix).

## 7. Project Layout
```
generator_team/
├── agents/            # All agent implementations
├── tools/             # Custom LangChain tools (PyDough executor, retriever)
├── pydough_data/      # Prompt templates, DB schema, cheatsheet, …
├── servers/           # Gradio / FastAPI endpoints
└── requirements.txt
```

---

