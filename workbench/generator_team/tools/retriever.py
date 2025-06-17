from typing import List, Optional
from google.oauth2 import service_account
from llama_index.embeddings.vertex import VertexTextEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.tools import QueryEngineTool
from langchain.tools import Tool
import os
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from chromadb.errors import NotFoundError

# Load environment variables from .env file
load_dotenv()

class RetrieverTool:
    def __init__(
        self,
        input_files: List[str],
        collection_name: str = "default_collection",
        project_id: Optional[str] = None,
        location: str = "us-central1",
        model_name: str = "text-embedding-005",
        top_k: int = 4,
        credentials_path: str = "/mnt/c/Users/david/bodo/vertex-embed-client.json"
    ):
        """Initialize the RetrieverTool with configuration for document retrieval.
        
        Args:
            input_files: List of file paths to load and index
            collection_name: Name for the Chroma collection
            project_id: GCP project ID (if None, uses GOOGLE_CLOUD_PROJECT env var)
            location: GCP location for Vertex AI
            model_name: Vertex AI embedding model name
            top_k: Number of similar documents to retrieve
            credentials_path: Path to the service account credentials JSON file
        """
        self.input_files = input_files
        self.collection_name = collection_name
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location
        self.model_name = model_name
        self.top_k = top_k
        self.credentials_path = credentials_path
        
        # Initialize components
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize the embedding model, load documents, and create the index."""
        # Load credentials from service account file
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path
        )
        
        # Initialize embedder with service account credentials
        self.embedder = VertexTextEmbedding(
            model_name=self.model_name,
            project=self.project_id,
            location=self.location,
            credentials=credentials
        )
        
        # Initialize ChromaDB client and collection
        chroma_client = chromadb.Client()
        try:
            self.collection = chroma_client.get_collection(self.collection_name)
        except (ValueError, NotFoundError):
            # Create new collection if it doesn't exist
            self.collection = chroma_client.create_collection(self.collection_name)
        
        # Load documents
        self.docs = SimpleDirectoryReader(input_files=self.input_files).load_data()
        
        # Create vector index
        self.index = VectorStoreIndex.from_documents(
            self.docs,
            embed_model=self.embedder,
            vector_store=ChromaVectorStore(self.collection),
        )
        
        # Create query engine
        self.query_engine = self.index.as_query_engine(similarity_top_k=self.top_k)
        
    def get_tool(self, name: str = "document_kb", description: str = "Semantic search over indexed documents"):
        """Get a tool function configured with the current index.
        
        Args:
            name: Name for the tool
            description: Description of the tool's functionality
            
        Returns:
            A LangChain Tool that can be used with an agent
        """
        query_engine = self.query_engine
        
        def search_documents(query: str) -> str:
            """Search documents using the query engine."""
            response = query_engine.query(query)
            return str(response)
            
        return Tool(
            name=name,
            func=search_documents,
            description=description,
            return_direct=False
        ) 