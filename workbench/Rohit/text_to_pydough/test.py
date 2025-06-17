#!/usr/bin/env python3

"""
Test script for LLM structured output functionality using simonw's llm library.
This script tests the conversion of natural language queries to PyDough code.
"""

import json
from pydantic import BaseModel
from typing import Optional
import llm

# Define Pydantic model for structured LLM output
class PyDoughResponse(BaseModel):
    """Structured response from LLM."""
    code: str
    explanation: Optional[str] = None

def main():
    """Test the LLM structured output functionality."""
    # Get the Gemini model
    model = llm.get_model("gemini-2.5-pro-preview-05-06")
    
    # Simple test query
    test_query = "Show me all customers who have more than 1000 shares of any stock"
    
    # Test prompt 
    prompt = f"""
# Task: Convert this natural language query into PyDough code for a Broker database:
"{test_query}"

# Example Schema:
Broker database has tables for Customers, Transactions, and Stocks.

# Example PyDough code:
```python
result = Broker.Customer.CALCULATE(
    *  # Select all fields
)
```

# Your task:
Return PyDough code that answers the query.
Make sure to return a variable named 'result' with the correct PyDough query.
"""
    
    print(f"Testing structured output with query: {test_query}")
    print("\nSending to LLM...")
    
    try:
        # Attempt structured output
        response = model.prompt(prompt, schema=PyDoughResponse)
        response_data = json.loads(response.text())
        
        print("\nStructured LLM Response:")
        print(json.dumps(response_data, indent=2))
        
        # Extract the code
        if "code" in response_data:
            print("\nExtracted PyDough code:")
            print(response_data["code"])
        
        # Check for explanation
        if "explanation" in response_data and response_data["explanation"]:
            print("\nExplanation:")
            print(response_data["explanation"])
            
        print("\n✅ Structured output test successful!")
    except Exception as e:
        print(f"\n❌ Error with structured output: {str(e)}")
        print("Falling back to unstructured output:")
        
        # Fallback to unstructured output
        response = model.prompt(prompt)
        print(response)

if __name__ == "__main__":
    main()