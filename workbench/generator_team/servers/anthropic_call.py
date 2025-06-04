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
MODEL_ID ="claude-3-7-sonnet@20250219"              # GA revision tag

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

def get_available_endpoints() -> list[dict]:
    """Fetch available endpoints from GCP."""
    try:
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = "us-central1"
        
        if not project:
            log.warning("GCP project not set in environment variables")
            return []
            
        # Initialize Vertex AI
        vertexai.init(project=project, location=location)
        
        # Initialize the Endpoint client
        client = aiplatform.EndpointServiceClient(
            client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        )
        
        parent = f"projects/{project}/locations/{location}"
        log.info(f"Listing endpoints from parent: {parent}")
        
        endpoints = []
        for ep in client.list_endpoints(parent=parent):
            endpoint_info = {
                "name": ep.name,
                "display_name": ep.display_name,
                "deployed_models": []
            }
            
            for dm in ep.deployed_models:
                model_info = {
                    "id": dm.id,
                    "model": dm.model
                }
                endpoint_info["deployed_models"].append(model_info)
            
            endpoints.append(endpoint_info)
            log.info(f"Found endpoint: {ep.display_name}")
        
        log.info(f"Found {len(endpoints)} endpoints")
        return endpoints
    except Exception as e:
        log.error(f"Error fetching GCP endpoints: {str(e)}", exc_info=True)
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
    
    # Get available endpoints
    endpoints = get_available_endpoints()
    
    # Print endpoint results
    if endpoints:
        log.info("\nAvailable endpoints:")
        for i, ep in enumerate(endpoints, 1):
            log.info(f"\n{i}. {ep['display_name']} — {ep['name']}")
            for dm in ep['deployed_models']:
                log.info(f"   deployed_model.id : {dm['id']}")
                log.info(f"   ↳ parent Model     : {dm['model']}")
    else:
        log.warning("No endpoints found or error occurred")

if __name__ == "__main__":
    main() 