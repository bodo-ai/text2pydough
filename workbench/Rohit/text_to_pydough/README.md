# PyDough Query Processor

A robust tool for generating, executing, and managing PyDough code using natural language queries and LLMs (Large Language Models).

## Overview

This project allows you to:
- Take a natural language query (e.g., "List all customers and their email addresses")
- Use an LLM (Gemini via the `llm` package) to generate PyDough code for your data domain
- Automatically adapt, save, and execute the generated code
- Save all results, code, SQL, and outputs in a structured way for easy review

## Features
- **Multi-domain support**: Handles multiple data domains (Broker, Dealership, DermTreatment, Ewallet, TPCH) with intelligent detection
- **LLM-powered**: Uses simonw's `llm` package with:
  - Gemini 2.5 Pro for code generation with structured output
  - Gemini 2.0 Flash for domain detection
- **Interactive and CLI modes**: Run interactively or via command-line arguments
- **Comprehensive results management**: All generated code, outputs, SQL, and errors are saved in the `results/` directory
- **Optional code review**: Optionally send generated code back to the LLM for review and improvement
- **Robust error handling**: Clear error messages and logs for troubleshooting
- **Category-based queries**: Process queries by specific category (e.g., Broker, Dealership, etc.)

## How It Works

The script processes natural language queries through several key steps:

### 1. Structured Output with Pydantic

The core of the system uses Pydantic models for reliable structured output from the LLM:

```python
# Define Pydantic model for structured LLM output
class PyDoughResponse(BaseModel):
    """Structured response from LLM."""
    code: str
    explanation: Optional[str] = None
```

This ensures that responses are parsed into a predictable schema rather than using error-prone regex extraction. When calling the LLM:

```python
# Get structured response with proper schema
response = model.prompt(prompt, schema=PyDoughResponse)
data = json.loads(response.text())
pydough_code = data["code"]
```

### 2. Domain Detection

The system intelligently detects which database domain a query is targeting:

- **LLM-based detection**: Uses a Pydantic model to extract structured responses:
  ```python
  class DomainDetection(BaseModel):
      domain: str
      confidence: float = 1.0
      reasoning: Optional[str] = None
  ```

- **Keyword-based fallback**: If LLM detection fails, falls back to keyword matching

### 3. Query Processing Flow

1. **Domain detection**: Determines the appropriate database domain
2. **Prompt construction**: Creates a domain-specific prompt with schema information
3. **LLM code generation**: Sends prompt to LLM with structured output schema
4. **Code adaptation**: Wraps generated PyDough code with proper imports and context
5. **Optional code review**: Sends code back to LLM for improvement using another Pydantic model
6. **Execution**: Runs the code and captures outputs
7. **Results storage**: Saves all artifacts (code, output, SQL, errors) to the `results/` directory

### 4. Interactive vs. CLI Mode

The system provides two interfaces:
- **Interactive mode**: Guided menu system for exploring queries and domains
- **CLI mode**: Command-line arguments for automation and scripting

## File Structure

```
project_root/
│
├── pydough_query_processor.py   # Main script
├── test.py                      # Test script for LLM structured output
├── queries.csv                  # List of natural language queries by category
├── cheatsheet.md                # PyDough syntax and usage guide
├── defog_broker.md              # Broker domain schema documentation
├── data/                        # Contains .json and .db files for each domain
│   ├── Broker_graph.json
│   ├── Broker.db
│   ├── Dealership_graph.json    # Additional domain graph files
│   ├── Dealership.db
│   ├── DermTreatment_graph.json
│   ├── DermTreatment.db
│   ├── Ewallet_graph.json
│   ├── Ewallet.db
│   ├── tpch_demo_graph.json
│   └── tpch.db
├── results/                     # All generated code, outputs, SQL, and logs
│   ├── [domain]_query_*.py      # Domain-specific query Python files
│   ├── query_result_*.json
│   ├── output_*.txt
│   ├── sql_*.sql
│   └── error_*.txt
└── README.md                    # This file
```

## Usage

### 1. Install Requirements

- Python 3.8+
- Install dependencies (the script will auto-install `llm`, `llm-gemini`, `pandas`, `tqdm`, `pydantic` if missing)
- Set up your Gemini API key:
  ```
  llm keys set gemini
  ```

### 2. Prepare Data
- Ensure your `data/` directory contains the correct `.json` and `.db` files for each domain.
- Make sure `queries.csv`, `cheatsheet.md`, and domain-specific schema files are present.

### 3. Run the Script

#### **Interactive Mode (Recommended for Exploration)**
```
python pydough_query_processor.py
```
- Presents a menu to select categories, queries, enter custom queries, choose domains, and toggle code review.

#### **Command-Line Mode (For Automation or Scripting)**

- **Run a specific query and execute the generated code:**
  ```
  python pydough_query_processor.py --query "List all customers and their email addresses" --execute
  ```

- **List all available query categories:**
  ```
  python pydough_query_processor.py --list-categories
  ```

- **Process queries from a specific category:**
  ```
  python pydough_query_processor.py --category Dealership --execute
  ```

- **Batch process the first N queries from a category:**
  ```
  python pydough_query_processor.py --category DermTreatment --batch 5 --execute
  ```

- **Force a specific domain:**
  ```
  python pydough_query_processor.py --query "List all transactions" --domain Ewallet --execute
  ```

- **Enable LLM code review:**
  ```
  python pydough_query_processor.py --query "..." --execute --review
  ```

### 4. Results and Artifacts

All generated files are saved in the `results/` directory:
- **query_result_*.json**: Full record of the query, generated code, LLM response, execution results, and file paths
- **[domain]_query_*.py**: The generated Python code (ready to run)
- **output_*.txt**: The full output (stdout) from running the code
- **sql_*.sql**: The SQL query generated by PyDough (if available)
- **error_*.txt**: Any error output from failed executions

## Domain Detection

The system uses two methods to detect which domain a query is about:

1. **LLM-based detection** (primary): Uses Gemini 2.0 Flash to analyze the query text and determine the most appropriate domain.
2. **Keyword-based detection** (fallback): If LLM detection fails, falls back to keyword matching to identify the domain.

This detection system allows you to use natural language queries without explicitly specifying the domain.

## Troubleshooting

- **Missing files**: The script will check for required files and print clear errors if any are missing.
- **No results or output**: Make sure you use the `--execute` flag or answer "y" to execution prompts in interactive mode.
- **LLM errors**: Ensure your Gemini API key is set and you have internet access.
- **Database errors**: Check that your `.db` and `.json` files are correct and in the `data/` directory.
- **Domain detection issues**: If automatic detection chooses the wrong domain, you can force a specific domain with the `--domain` flag.

## Extending the Project
- Add new domains by updating the `DOMAINS` dictionary with new entries including keywords, metadata file path, and database file path.
- Add new query categories to `queries.csv`.
- Improve prompt engineering in `create_prompt` for better LLM results.
- Add domain-specific schema documentation (e.g., `defog_ewallet.md`) for each domain.
