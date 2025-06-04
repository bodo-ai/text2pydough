from typing import Dict, TypedDict, Annotated
from langgraph.graph import Graph, StateGraph
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure LangGraph runtime
os.environ["LANGGRAPH_RUNTIME"] = "in_memory"
os.environ["LANGGRAPH_API_VARIANT"] = "local_dev"
os.environ["LANGGRAPH_STUDIO_URL"] = "http://127.0.0.1:2024"
os.environ["LANGGRAPH_STUDIO_ENABLED"] = "true"
os.environ["LANGSMITH_API_KEY"]="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"

# Define the state
class AgentState(TypedDict):
    messages: list[HumanMessage | AIMessage]

# Define the nodes
def agent(state: AgentState) -> AgentState:
    """Agent node that processes messages and generates responses."""
    try:
        # Add your agent logic here
        logger.info("Processing message in agent node")
        return state
    except Exception as e:
        logger.error(f"Error in agent node: {str(e)}")
        raise

# Create the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", agent)

# Add edges
workflow.add_edge("agent", "agent")

# Set the entry point
workflow.set_entry_point("agent")

# Compile the graph
app = workflow.compile()

if __name__ == "__main__":
    try:
        logger.info("Starting LangGraph application")
        # Example usage
        result = app.invoke({"messages": [HumanMessage(content="Hello!")]})
        logger.info(f"Result: {result}")
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise 