# Text2pydough

Text2Pydough is a comprehensive AI evaluation system that enables Large Language Models (LLMs) to generate [PyDough](https://github.com/bodo-ai/PyDough) code directly from natural language queries. It is designed to assess and demonstrate the models' capabilities in translating text to PyDough code effectively.

## What is text2Pydough? 

Text2Pydough is an AI-powered system that evaluates and demonstrates how effectively Large Language Models (LLMs) can translate natural language queries into PyDough code. [PyDough](https://github.com/bodo-ai/PyDough) is a domain-specific language (DSL) for database operations that offers an alternative, more intuitive syntax to SQL for querying relational databases. Text2Pydough provides a complete ecosystem that includes:
- AI Model Evaluation: Parallel evaluation frameworks to test the performance of various AI providers in generating accurate PyDough code from natural language.
- Interactive Demonstrations: Web-based applications that allow real-time PyDough code generation from user inputs.
- Multi-Provider AI Integration: A flexible abstraction layer supporting multiple LLM providers, including Claude, Gemini, Azure OpenAI, DeepSeek, and others.

### Objectives 

- Develop a reliable tool capable of converting natural language into PyDough code.
- Ensure high accuracy in the code generated according to user requirements. 
- Guarantee that the generated PyDough statements are coherent and aligned with the user's intent. 
- Leverage PyDough to produce simple, efficient, and optimized queries. 
- Simplify the processing of metadata within the system.

# Learning about Text2pydough 

The prompt evaluation script consists of multiple parallel implementations that evaluate AI models' PyDough code generation capabilities through automate pipelines.  The prompt evaluation includes ensemble logic and parallel model execution. This script benchmarks AI models' ability to generate correct database queries from natural language questions

This is the prompt evaluation workflow:

1.	Argument parsing: The script accepts command-line arguments specifying database paths, model configurations, prompt files, and execution parameters.
2.	Mlflow setup: Initializes MLflow tracking with remote URI and authentication token to log experiments and model artifacts.
3.	Database metadata: Prepares database schema information by generating JSON metadata files for each database if they don't exist, creating a mapping structure for SQL query generation.
4.	Questions processing: Loads test questions from CSV and processes them either sequentially or in parallel across multiple AI models (Claude, Gemini, etc.) using threading for concurrent execution. 
5.	Ensemble selection: When running multiple models in parallel, implements an ensemble approach that compares DataFrame outputs between models to find consensus or falls back to the most reliable model (preferring Gemini).
6.	Result evaluation: Executes generated Python code against test databases, compares outputs with expected results, and categorizes results as "Match" or other comparison outcomes.
7.	Metrics calculation: Computes performance statistics including match percentages by difficulty, complexity, and database combinations, generating detailed breakdowns for analysis.
8.	MlFlow loggin: Records all experiment parameters, metrics, artifacts (CSV files, distribution reports), and logs the final model with associated prompt and script files for reproducibility.


## Requirements

- **WSL** (Windows Subsystem for Linux) must be installed with a Linux distribution (Ubuntu is recommended). 
  Installation instructions: https://learn.microsoft.com/en-us/windows/wsl/install

- (Optional but recommended) Miniconda or Anaconda for environment management: 
  https://www.anaconda.com/docs/getting-started/miniconda/install#linux

## Installation Guide

1. **Clone the Repository** 
   ```bash
   git clone https://github.com/bodo-ai/text2pydough.git
   cd text2pydough/
   ```

2. **Install Miniconda (if not already installed)**  
   ```bash
   mkdir -p ~/miniconda3
   wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
   bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
   rm ~/miniconda3/miniconda.sh
   source ~/miniconda3/bin/activate
   conda init --all
   ```
   > After running `rm ~/miniconda3/miniconda.sh`, close and reopen the terminal.

3. **Create and Activate the Virtual Environment**  
   ```bash
   conda env create -f environment.yml
   conda activate aisuite_deepseek
   ```

4. **Install Additional Dependencies**  
   ```bash
   pip install google.genai
   pip install mistralai
   ```
   
## System Structure Overview

This section provides an overview of the core directories that make up the `text2pydough` project, including their purpose, key components, and how they fit into the overall pipeline for natural language to PyDough code generation.


### LCARS Demo

The `LCARS` directory contains an interactive demo system for generating PyDough code from natural language queries. It is built entirely in Python and Jupyter notebooks, and serves as a hands-on demonstration of the system’s capabilities, using real-time AI model responses and the TPCH database schema. To provide a user-friendly interface for exploring how LLMs generate PyDough code, translate it into SQL, and return results.

- [LCARS DEMO](https://github.com/bodo-ai/text2pydough/tree/main/workbench/LCARS)

### lcar_lab

The `lcar_lab` directory is a research and experimentation suite for training, evaluating, and improving AI models for PyDough generation. It contains all infrastructure necessary for ML experimentation, including tracking, data processing, and automatic evaluation.

- [LCAR_LAB](https://github.com/bodo-ai/text2pydough/tree/main/workbench/lcar_lab)