from typing import List, Optional
import os
from dotenv import load_dotenv
import vertexai
from vertexai.language_models import TextEmbeddingModel
import logging
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def check_authentication():
    """Check if Google Cloud authentication is properly set up."""
    try:
        credentials, project = default()
        logger.info(f"Successfully authenticated with project: {project}")
        return True
    except DefaultCredentialsError as e:
        logger.error("Authentication failed. Please run 'gcloud auth application-default login'")
        raise

class VertexAIEmbeddings:
    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "text-embedding-005"
    ):
        """Initialize the Vertex AI Embeddings client."""
        logger.info(f"Initializing VertexAIEmbeddings with project_id: {project_id}")
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        
        # Check authentication first
        check_authentication()
        
        # Initialize Vertex AI
        logger.info("Initializing Vertex AI...")
        try:
            vertexai.init(
                project=project_id,
                location=location,
            )
            logger.info("Vertex AI initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {str(e)}")
            raise
        
        # Initialize the model
        logger.info(f"Loading model: {model_name}")
        try:
            self.model = TextEmbeddingModel.from_pretrained(model_name)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise

    def get_embeddings(
        self,
        texts: List[str],
        dimensionality: Optional[int] = None
    ) -> List[List[float]]:
        """Get embeddings for a list of texts."""
        try:
            logger.info(f"Getting embeddings for {len(texts)} texts")
            
            # Get embeddings using the model
            logger.info("Calling model.get_embeddings()...")
            embeddings = self.model.get_embeddings(texts=texts)
            logger.info("Successfully received embeddings from model")
            
            # Extract values from embeddings
            logger.info("Processing embedding values...")
            result = []
            for emb in embeddings:
                # Debug print to see the structure
                logger.info(f"Embedding type: {type(emb)}")
                logger.info(f"Embedding attributes: {dir(emb)}")
                # Get the values
                values = emb.values
                logger.info(f"Values type: {type(values)}")
                logger.info(f"Values length: {len(values)}")
                result.append(values)
            
            logger.info(f"Successfully processed {len(result)} embeddings")
            return result
            
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}", exc_info=True)
            raise

def test_embeddings():
    """Test the Vertex AI Embeddings functionality."""
    logger.info("Starting embeddings test...")
    
    # Get project ID from environment variable
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        logger.error("GOOGLE_CLOUD_PROJECT environment variable not set")
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")
    
    logger.info(f"Using project ID: {project_id}")
    
    try:
        # Initialize the embeddings client
        embeddings_client = VertexAIEmbeddings(project_id=project_id)
        
        # Test texts
        test_texts = [
            "What is machine learning?",
            "How does deep learning work?",
            "Explain neural networks"
        ]
        
        # Get embeddings
        logger.info("Requesting embeddings...")
        embeddings = embeddings_client.get_embeddings(texts=test_texts)
        
        # Print results
        print("\n=== Embeddings Test Results ===")
        for i, (text, embedding) in enumerate(zip(test_texts, embeddings)):
            print(f"\nText {i+1}: {text}")
            print(f"Embedding dimension: {len(embedding)}")
            print(f"First 5 values: {embedding[:5]}")
            print(f"Last 5 values: {embedding[-5:]}")
            print(f"Min value: {min(embedding)}")
            print(f"Max value: {max(embedding)}")
            print(f"Mean value: {sum(embedding)/len(embedding):.6f}")
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        print(f"Test failed: {str(e)}")
        raise  # Re-raise the exception to see the full traceback

if __name__ == "__main__":
    print("Starting embeddings test script...")
    try:
        test_embeddings()
        print("\nTest script completed successfully.")
    except Exception as e:
        print(f"Script failed with error: {str(e)}")
        raise  # Re-raise to see the full traceback 