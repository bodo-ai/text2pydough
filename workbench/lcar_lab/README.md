# LCAR_LAB

`lcar_lab` is a comprehensive research and development lab designed to automate the generation, evaluation, and training of AI models that produce PyDough code from natural language queries. It contains all systems needed to support a continuous cycle of dataset creation, model evaluation, and fine-tuning.

## Purpose

The main goal of `lcar_lab` is to provide an integrated experimentation ecosystem where models can be:
- Prompted with natural language queries
- Evaluated for correctness against SQL references
- Trained using validated and enriched datasets
- Iteratively improved through automated feedback loops

Each submodule in `lcar_lab` serves a specific purpose in this AI development pipeline.

## Core Components

### 1. `labeling_agent/` — Automated Labeling System

The `labeling_agent` subdirectory implements an end-to-end pipeline for generating and validating PyDough code using LLMs. It compares outputs against reference SQL and provides structured feedback.

**Key Features:**
- Asynchronous orchestrator with concurrency control
- Multi-step feedback loops to retry failed generations
- Integration with ReAct agents and PyDough execution tools
- Validation using `SQLEvaluatorAgent` for numeric DataFrame comparison

**Main Scripts:**
- `async_orchestrator.py`: Manages parallel processing of queries
- `generator_agent_with_feedback.py`: Converts queries to PyDough code using LLMs
- `evaluator_agent.py`: Evaluates output vs. SQL ground truth
- `execution_tools.py`: Executes generated PyDough code

**Output:**
- Labeled CSVs with generated code, feedback, evaluation metrics, and metadata
- Timestamped folders separating passed and failed cases


### 2. `mlflow_experiments/` — Model Evaluation and Benchmarking

This submodule implements an MLflow-based evaluation framework for tracking and comparing AI model performance across different providers and configurations.

**Key Features:**
- Parallel evaluation with `ThreadPoolExecutor`
- Integration with Claude, Gemini, DeepSeek, and other providers
- Consensus logic for ensemble evaluation
- Full MLflow logging of metrics and artifacts

**Main Scripts:**
- `prompt_evaluation.py`: Main driver for experiment runs
- Prompt templates and SQL datasets in `data/prompts/`

**Metrics Tracked:**
- Success rates by difficulty and schema
- Categorized results (Match, No Match, Query Error)
- Distribution charts and provider comparisons

**Output:**
- MLflow dashboards with reproducible experiment metadata


### 3. `training/` — Dataset Preparation for Fine-Tuning

The `training` directory focuses on preparing high-quality training datasets using labeled outputs from `labeling_agent`. It enriches training context using RAG (Retrieval-Augmented Generation) and organizes data for model fine-tuning.

**Key Features:**
- Async data processing with rate-limited API usage
- RAG-based context augmentation
- Output in multiple formats (JSONL, CSV, Markdown)

**Main Scripts:**
- `generate_finetuning_data_gemini.py`: Creates fine-tuning datasets from validated results
- `merge_schema_data.py`: Combines prompts with database metadata
- `utils/`: Helpers for testing datasets, stratified splits, and dataset merging

**Output:**
- Structured datasets by timestamp with training/validation splits
- Metadata logs with counts, file paths, and configuration settings


## Workflow Overview

1. **Input**: A CSV with natural language queries and reference SQL queries
2. **Generation**: The generator agent produces PyDough code using an LLM
3. **Execution**: The code is executed and compared to SQL using the evaluator
4. **Iteration**: If the result is incorrect, the system applies feedback and retries
5. **Labeling**: Outputs are saved with metrics and feedback for further use
6. **Training**: Validated examples are enriched and prepared for fine-tuning
7. **Evaluation**: Trained models are benchmarked in `mlflow_experiments`
8. **Improvement**: Insights feed back into prompt design and model choice

## Folder Structure

lcar_lab/
├── labeling_agent/ # Core automated feedback + validation     system
│ ├── async_orchestrator.py
│ ├── generator_agent_with_feedback.py
│ ├── evaluator_agent.py
│ └── execution_tools.py
├── mlflow_experiments/ # MLflow-based evaluation framework
│ ├── prompt_evaluation.py
│ └── data/prompts/
├── training/ # Dataset generation and enrichment pipeline
│ ├── generate_finetuning_data_gemini.py
│ ├── merge_schema_data.py
│ └── utils/


## Output Artifacts

- CSVs with evaluation logs and labeling results
- JSONL datasets for fine-tuning
- MLflow dashboards with full metric tracking
- Metadata files (schema, prompt config, cheat sheets)

## Key Differences with Other Modules

| Module            | Focus                          | Output                           |
|-------------------|--------------------------------|----------------------------------|
| `labeling_agent`  | Automated data labeling        | CSVs with labeled PyDough code   |
| `training`        | Dataset preparation            | JSONL/CSV for model fine-tuning  |
| `mlflow_experiments` | Systematic model evaluation | Metrics and MLflow tracking      |
| `LCARS`           | User-facing demo               | Interactive Streamlit app        |

## Related Wiki Pages

- [MLflow Experiments](https://github.com/bodo-ai/text2pydough/tree/main/workbench/lcar_lab/mlflow_experiments)
- [Training and Data Systems](https://github.com/bodo-ai/text2pydough/tree/main/workbench/lcar_lab/training)
- [Labeling Agent Overview](https://github.com/bodo-ai/text2pydough/tree/main/workbench/lcar_lab/labeling_agent)

## Final Notes

`lcar_lab` forms the experimental backbone of the `text2pydough` ecosystem. Its feedback-driven architecture ensures that every model iteration is built on validated, high-quality data. By automating generation, evaluation, and training in a unified pipeline, `lcar_lab` enables reproducible, scalable, and data-driven improvement of AI systems for code generation.
