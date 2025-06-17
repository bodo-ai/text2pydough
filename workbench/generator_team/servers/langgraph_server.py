from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, Union
import uvicorn
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent import PydoughGeneratorAgent, AgentState

from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uuid
import json
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="PyDough Generator Agent API")

# Add CORS middleware to allow LangGraph Studio to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize the agent
db_path = os.getenv("DB_PATH", "C:/Users/david/bodo/TPCH/test_data/tpch.db")
metadata_path = os.getenv("METADATA_PATH", "C:/Users/david/bodo/TPCH/test_data/tpch_demo_graph.json")

agent = PydoughGeneratorAgent(
    db_path=db_path,
    metadata_path=metadata_path
)

# Store threads in memory
threads_store: Dict[str, Dict[str, Any]] = {}

@app.post("/assistants/search")
async def assistants_search(payload: dict = Body(...)):
    """Search for available assistants."""
    return [{
        "assistant_id": "pydough-agent",
        "name": "PyDough Generator Agent",
        "description": "An agent that generates and executes PyDough code based on natural language questions",
        "config": {},  # important – Studio filters on this
    }]

@app.post("/threads")
async def create_thread():
    """Create a new thread."""
    thread_id = str(uuid.uuid4())
    threads_store[thread_id] = {"created_at": datetime.utcnow()}
    return {"thread_id": thread_id}

@app.post("/threads/{thread_id}/runs/stream")
async def stream_run(thread_id: str, body: dict = Body(...)):
    """Stream updates for a run in a specific thread."""
    if thread_id not in threads_store:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    assistant_id = body["assistant_id"]
    messages = body["input"]["messages"]
    stream_mode = body.get("stream_mode", "updates")

    async def event_generator():
        # Start-of-run metadata
        yield f"event: start\ndata: {json.dumps({'run_id': str(uuid.uuid4())})}\n\n"

        # Process the messages and stream results
        try:
            # Assuming agent.generate_and_execute_stream is implemented
            async for chunk in agent.generate_and_execute_stream(messages, mode=stream_mode):
                yield f"event: {chunk.event}\n" \
                      f"data: {json.dumps(chunk.data)}\n\n"
                await asyncio.sleep(0)  # let the loop breathe
        except Exception as e:
            logger.error(f"Error in stream_run: {str(e)}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

        # Tell Studio we're done
        yield "event: end\ndata: {}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@app.get("/")
async def root():
    return {
        "message": "PyDough Generator Agent API",
        "endpoints": {
            "assistants/search": "/assistants/search - Search for assistants",
            "threads": "/threads - Create and manage threads",
            "threads/runs/stream": "/threads/{thread_id}/runs/stream - Stream run updates",
            "docs": "/docs - API documentation"
        }
    }

if __name__ == "__main__":
    logger.info("Starting LangGraph server on port 2024")
    uvicorn.run(app, host="127.0.0.1", port=2024) 