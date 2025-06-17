# Pydough Multi-Agent Labeling System

This project implements a multi-agent system for Pydough code generation and evaluation. The system consists of two main agents:

1. **Pydough Generator Agent**: Generates and executes Pydough code based on natural language prompts
2. **Pydough Evaluator Agent**: Validates generated code against reference SQL queries and provides feedback

## Features

- Natural language to Pydough code conversion
- Automatic code execution and result comparison
- Feedback loop between generator and evaluator agents
- Parallel processing for efficient evaluation
- Progress tracking with visual feedback
- Error handling and debugging support

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root with your Google API key:
```bash
GOOGLE_API_KEY="your-api-key-here"
```

3. Configure your database and metadata paths:
```python
db_path = "path/to/your/database.db"
metadata_path = "path/to/your/metadata.json"
cheatsheet_path = "path/to/your/cheatsheet.md"
```

## Usage

```python
from generator_agent_with_feedback import PydoughGeneratorAgent
from evaluator_agent import SQLEvaluatorAgent
import pandas as pd

# Initialize the agents
db_path = "path/to/your/database.db"
metadata_path = "path/to/your/metadata.json"
cheatsheet_path = "path/to/your/cheatsheet.md"

generator_agent = PydoughGeneratorAgent(db_path, metadata_path, cheatsheet_path)
evaluator_agent = SQLEvaluatorAgent(f"sqlite:///{db_path}")

# Process a single question
question = "Show me the total sales by product category for the last quarter"
sql_query = "SELECT category, SUM(sales) FROM products GROUP BY category"

result = await process_single_question(
    question=question,
    sql_query=sql_query,
    generator_agent=generator_agent,
    evaluator_agent=evaluator_agent,
    question_id=1
)
```

## Agent Capabilities

### Pydough Generator Agent
- Converts natural language to Pydough code
- Executes code and returns results
- Handles feedback from evaluator
- Optimizes code based on evaluation results
- Supports multiple feedback loops for improvement

### Pydough Evaluator Agent
- Validates Pydough results against SQL ground truth
- Compares DataFrame outputs for equivalence
- Provides detailed feedback for improvements
- Handles large datasets efficiently
- Supports parallel processing of multiple questions

## System Architecture

The system uses a feedback loop architecture:
1. Generator creates Pydough code from natural language
2. Evaluator compares results with SQL ground truth
3. If results don't match, evaluator provides feedback
4. Generator uses feedback to improve the code
5. Process repeats until match or max iterations reached


## Requirements

- Python 3.8+
- SQLite database
- Metadata graph JSON file
- Pydough cheatsheet markdown file
- Required Python packages (see requirements.txt)

