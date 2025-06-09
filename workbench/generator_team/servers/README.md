# PyDough Generator Agent Gradio Server

This server provides a web interface for interacting with the PyDough Generator Agent using Gradio and FastAPI.

## Features

- Interactive chat interface for querying the agent
- Model selection from multiple providers (GCP, AWS, Gemini, Mistral, Anthropic)
- System prompt template management
  - View and edit prompt templates
  - Save changes to templates
  - Collapsible template editor
- Database selection
- Retriever file selection
- CSV data preview and management
- Configurable model parameters
  - Temperature
  - Top P
  - Top K
- Optional features
  - Include cheatsheet in context
  - Include schema in context
  - Enable SQL execution tools
  - Disable all tools

## Directory Structure

```
generator_team/
├── servers/
│   ├── gradio_server.py    # Main server implementation
│   ├── gcp_model_call.py   # GCP model integration
│   └── README.md          # This file
├── pydough_data/
│   ├── prompts/           # System prompt templates
│   └── pydough_files/     # Retriever files
└── TPCH/
    └── test_data/         # Database and metadata files
```

## Configuration

The server uses several environment variables for configuration:

- `MLFLOW_TRACKING_URI`: MLflow tracking server URI (default: "http://localhost:5000")
- `MLFLOW_TRACKING_TOKEN`: MLflow tracking token
- `EXPERIMENT_NAME`: Name of the MLflow experiment
- `DB_PATH`: Path to the SQLite database
- `METADATA_PATH`: Path to the metadata JSON file
- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `GOOGLE_CLOUD_LOCATION`: GCP location (default: "us-central1")

## Running the Server

1. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables (or use a .env file)

3. Run the server:
   ```bash
   python gradio_server.py
   ```

The server will start on port 2024 and provide a public URL for access.

## UI Components

### Model Selection
- Dropdown menu for selecting different models from various providers
- Supports GCP, AWS, Gemini, Mistral, and Anthropic models

### System Prompt Template
- Collapsible section for managing prompt templates
- Text editor for viewing and editing templates
- Save button for persisting changes
- Dropdown for selecting different template files

### Model Parameters
- Temperature slider (0.0 - 1.0)
- Top P slider (0.0 - 1.0)
- Top K slider (1 - 100)

### Optional Features
- Checkboxes for enabling/disabling various features
- SQL tools toggle
- Context inclusion options

### CSV Data Preview
- File upload for CSV files
- Configurable rows per page
- Column selection
- Load more functionality

## Development

### Adding New Models
1. Add the model to the appropriate model list in `gradio_server.py`:
   - `GEMINI_MODELS`
   - `MISTRAL_MODELS`
   - `ANTHROPIC_MODELS`
   - `AWS_MODELS`
   - `GCP_MODELS`

2. Update the model handling logic in `create_agent()` if needed

### Adding New Features
1. Add UI components in the Gradio interface
2. Update the `process_message()` function to handle new parameters
3. Modify the agent creation logic if needed

## Troubleshooting

### Common Issues

1. **MLflow Connection Issues**
   - Check if MLflow server is running
   - Verify MLFLOW_TRACKING_URI and MLFLOW_TRACKING_TOKEN

2. **Model Access Issues**
   - Verify GCP credentials
   - Check model availability in the selected region
   - Ensure proper permissions are set

