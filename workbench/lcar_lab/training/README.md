# PyDough Training Module

This module contains tools and data for training an LLM to generate PyDough code from natural language questions.

## Setup Instructions

### Option 1: Using venv (Python's built-in virtual environment)

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Option 2: Using Conda

1. Create a new conda environment:
```bash
conda create -n pydough python=3.10
conda activate pydough
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Environment Setup (for both options)

3. Set up environment variables:
Create a `.env` file in the training directory with:
```
# API Keys
GOOGLE_API_KEY=your_google_api_key_here
R2R_API_KEY=your_r2r_api_key_here

# Google Cloud Project Configuration
GCP_PROJECT=your_gcp_project_id
GCP_PROJECT_LOCATION=your_gcp_location  # e.g., us-central1
```

## Code Structure

### Core Components

- `basicQ_retrieve_pydough.py`: 
  - Handles retrieval of PyDough code for basic question patterns
  - Implements rate-limited API calls with retry logic
  - Processes questions in batches with progress tracking
  - Generates documentation using RAG (Retrieval-Augmented Generation)

- `retrieve_pydough.py`:
  - Core retrieval functionality for PyDough code generation
  - Extracts key terms from PyDough code
  - Creates RAG prompts for documentation generation
  - Processes the PyDough corpus and generates documentation

- `generate_finetuning_data_gemini.py`:
  - Generates training data using Google's Gemini model
  - Processes questions with database schemas
  - Implements async processing with rate limiting
  - Creates JSONL format training data with context

- `merge_schema_data.py`:
  - Merges database schema information with training data
  - Maps question IDs to database names
  - Combines schema JSON with processed data
  - Generates statistics about database distribution

### Supporting Directories

- `utils/`: Helper functions and utilities
- `training_data/`: Directory containing training datasets
- `graphs/`: JSON files containing graph schemas used in training
- `retriver/`: Components for retrieval operations

## Training Data Format

The training data follows the Gemini text tuning format, which is structured as a JSON object with the following components:

```json
{
  "systemInstruction": {
    "role": "system",
    "parts": [
      {
        "text": "You are an analytics expert and a proficient Pydough generator that creates Python code based on natural language descriptions."
      }
    ]
  },
  "contents": [
    {
      "role": "user",
      "parts": [
        {
          "text": "What is the total revenue by region?"
        }
      ]
    },
    {
      "role": "model",
      "parts": [
        {
          "text": "result = sales.CALCULATE(SUM(revenue)).GROUP_BY(region)"
        }
      ]
    }
  ]
}
```

### Dataset Components

1. **System Instruction**: Defines the model's role and behavior
   - Sets the context for PyDough code generation
   - Establishes the model as an analytics expert

2. **Contents**: Array of conversation turns
   - Each turn has a `role` ("user" or "model")
   - Each turn contains `parts` with the actual text
   - User turns contain natural language questions
   - Model turns contain PyDough code responses

### Data Storage

- Training datasets are stored in Cloud Storage buckets
- Files can be accessed via:
  - Cloud Storage URI (gs://)
  - Public HTTP/HTTPS URLs

### Sample Datasets

The module includes sample datasets for:
- Training: `gs://cloud-samples-data/ai-platform/generative_ai/sft_train_data.jsonl`
- Validation: `gs://cloud-samples-data/ai-platform/generative_ai/sft_validation_data.jsonl`

## Included Knowledge Bases

The following knowledge bases and queries are included:

- TPCH: the knowledge base used to describe the TPC-H schema.
    - Specific implementations of all 21 TPC-H queries.
    - Several additional custom queries using the same schema.
- Broker: the BROKER schema from the defog.ai database.
    - 7/10 of the basic questions from defog.ai in this schema.
    - 6/16 of the advanced questions from defog.ai in this schema.

## Generating Training Data

To generate new training data using the Gemini model:

1. Ensure you have set up your Google API key in the `.env` file
2. Run the generation script:
```bash
python generate_finetuning_data_gemini.py
```

The script will:
- Process questions from the corpus
- Generate PyDough code using Gemini
- Save the results in the training data directory

## Key Dependencies

- `google-genai`: For interacting with Google's Gemini model
- `pandas`: For data manipulation and CSV handling
- `sqlalchemy`: For database operations
- `r2r`: For retrieval and ranking operations
- `aiolimiter`: For rate limiting API calls


