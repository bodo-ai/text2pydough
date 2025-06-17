import os
import logging
from dotenv import load_dotenv
from langchain_google_vertexai.model_garden import ChatAnthropicVertex

# Load environment variables and configure logging
load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Constants for Vertex AI configuration
PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "solid-drive-448717-p8")
LOCATION = "us-east5"                                # Anthropic region
ENDPOINT = f"{LOCATION}-aiplatform.googleapis.com"   # belt & braces
MODEL_ID = "claude-3-7-sonnet@20250219"              # GA revision tag

def init_model() -> ChatAnthropicVertex:
    """Initialize the Claude model with the specified configuration."""
    return ChatAnthropicVertex(
        model_name=MODEL_ID,       # just the ID (wrapper adds publisher)
        project=PROJECT,
        location=LOCATION,
        api_endpoint=ENDPOINT,
        temperature=0.5,
        max_output_tokens=512,
        top_p=0.95,
        top_k=1,
    )

def get_available_models() -> list[str]:
    """Fetch available models from GCP using LangChain."""
    try:
        log.info("⚙️  initialising Claude 3.7 Sonnet on Vertex AI …")
        llm = init_model()
        
        # Test the model with a simple prompt
        reply = llm.invoke("Write a 3‑line Python function that reverses a string.")
        log.info("✅ model answered:\n%s", reply)
        
        # For now, we'll just return the Claude model since that's what we're using
        return [MODEL_ID]
        
    except Exception as e:
        log.error(f"Error initializing LangChain Vertex AI model: {str(e)}", exc_info=True)
        return []

def main() -> None:
    """Main function to test model initialization."""
    log.info("Starting model initialization test...")
    
    # Check if GCP project is set
    if not PROJECT:
        log.error("GOOGLE_CLOUD_PROJECT environment variable is not set")
        return
    
    log.info(f"Using GCP project: {PROJECT}")
    log.info(f"Using endpoint: {ENDPOINT}")
    log.info(f"Using location: {LOCATION}")
    
    # Get available models
    models = get_available_models()
    
    # Print model results
    if models:
        log.info("\nAvailable models:")
        for i, model in enumerate(models, 1):
            log.info(f"{i}. {model}")
    else:
        log.warning("No models found or error occurred")

if __name__ == "__main__":
    main() 