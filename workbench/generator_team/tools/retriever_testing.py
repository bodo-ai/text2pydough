from typing import List, Dict, Any
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain_google_vertexai import ChatVertexAI
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
from pathlib import Path
from retriever import RetrieverTool
import chromadb
import shutil

# Load environment variables
load_dotenv()

def create_test_documents():
    """Create test documents for the retriever."""
    # Create a test directory if it doesn't exist
    test_dir = Path("test_docs")
    test_dir.mkdir(exist_ok=True)
    
    # Create a test document with PyDough information
    with open(test_dir / "pydough_info.md", "w") as f:
        f.write("""
# PyDough Documentation

PyDough is a powerful data processing library that allows you to:
- Transform data using a graph-based approach
- Execute complex data transformations
- Handle large datasets efficiently

## Key Features
1. Graph-based transformations
2. Efficient execution
3. Easy to use API
        """)
    
    # Create another test document with examples
    with open(test_dir / "pydough_examples.md", "w") as f:
        f.write("""
# PyDough Examples

## Basic Example
```python
from pydough import transform_cell

# Transform a single cell
result = transform_cell("input_value", "transformation_rule")
```

## Advanced Example
```python
from pydough import Graph

# Create a transformation graph
graph = Graph()
graph.add_node("input", "source_data")
graph.add_node("transform", "transformation_rule")
graph.add_edge("input", "transform")
        """)
    
    return [str(test_dir / "pydough_info.md"), str(test_dir / "pydough_examples.md")]

def cleanup_test_environment():
    """Clean up test environment by removing test documents and Chroma collection."""
    # Remove test documents
    test_dir = Path("test_docs")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    # Delete test collection from Chroma
    try:
        chroma_client = chromadb.Client()
        chroma_client.delete_collection("test_collection")
    except Exception:
        pass  # Collection might not exist, which is fine

def test_retriever_tool():
    """Test the RetrieverTool with a simple agent."""
    # Clean up any existing test environment
    cleanup_test_environment()
    
    # Create test documents
    test_files = create_test_documents()
    
    # Initialize the retriever tool
    retriever = RetrieverTool(
        input_files=test_files,
        collection_name="test_collection",
        model_name="text-embedding-005",  # Updated to use new model
        credentials_path="/mnt/c/Users/david/bodo/vertex-embed-client.json"
    )
    
    # Get the retriever tool
    retriever_tool = retriever.get_tool(
        name="document_kb",
        description="Search PyDough documentation and examples"
    )
    
    # Initialize the LLM
    llm = ChatVertexAI(
        model="gemini-2.0-flash",
        temperature=0.7,
        max_tokens=8192,
        max_retries=6
    )
    
    # Create the system prompt
    system_prompt = """You are a helpful assistant that can search through PyDough documentation.
When you need information about PyDough, use the document_kb tool to search for relevant information.
Always provide accurate and helpful responses based on the documentation."""
    
    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("messages"),
        MessagesPlaceholder("agent_scratchpad")
    ])
    
    # Create the agent
    agent = create_openai_functions_agent(
        llm=llm,
        tools=[retriever_tool],
        prompt=prompt
    )
    
    # Create the agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=[retriever_tool],
        verbose=True
    )
    
    # Test queries
    test_queries = [
        "What are the key features of PyDough?",
        "Can you show me an example of how to use PyDough?",
        "How do I create a transformation graph in PyDough?"
    ]
    
    try:
        # Run the test queries
        for query in test_queries:
            print(f"\n=== Testing Query: {query} ===")
            try:
                result = agent_executor.invoke({
                    "messages": [HumanMessage(content=query)]
                })
                print(f"Response: {result['output']}")
            except Exception as e:
                print(f"Error: {str(e)}")
    finally:
        # Clean up after tests
        cleanup_test_environment()

if __name__ == "__main__":
    test_retriever_tool() 