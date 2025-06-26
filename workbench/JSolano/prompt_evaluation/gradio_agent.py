from gradio_client import Client
import json
import pandas as pd
import re

print("Starting gradio_agent.py")   
def extract_plain_text(result):
    """Extract plain text from the agent response."""
    if not result or len(result) < 2:
        return ""
    
    assistant_response = result[1].get('content', '')
    return assistant_response

def extract_json(result):
    """Extract pure JSON from the agent response."""
    plain_text = extract_plain_text(result)
    if not plain_text:
        return None

    # Look for JSON content within ```json code blocks
    json_pattern = r'```json\s*(.*?)\s*```'
    match = re.search(json_pattern, plain_text, re.DOTALL)
    
    json_str = ""
    if match:
        json_str = match.group(1).strip()
    else:
        # If no markdown, maybe the whole response is JSON.
        # Let's find the first '{' or '[' and try to parse from there.
        brace_pos = plain_text.find('{')
        bracket_pos = plain_text.find('[')
        
        start_pos = -1
        
        if brace_pos != -1 and bracket_pos != -1:
            start_pos = min(brace_pos, bracket_pos)
        elif brace_pos != -1:
            start_pos = brace_pos
        elif bracket_pos != -1:
            start_pos = bracket_pos
            
        if start_pos != -1:
            json_str = plain_text[start_pos:]

    if not json_str:
        return None

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # The string may have trailing characters, so let's try to parse until we can't anymore
        decoder = json.JSONDecoder()
        try:
            val, idx = decoder.raw_decode(json_str)
            return val
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return None

def extract_dataframe(json_data):
    """Convert extracted JSON to a Pandas DataFrame."""
    if json_data is None:
        return None
    
    try:
        # Handle different JSON structures
        if isinstance(json_data, list):
            df = pd.DataFrame(json_data)
        elif isinstance(json_data, dict):
            df = pd.DataFrame([json_data])
        else:
            print(f"Unsupported JSON structure for DataFrame: {type(json_data)}")
            return None
        
        return df
    except Exception as e:
        print(f"Error converting to DataFrame: {e}")
        return None

def run_question(question, server_URL="http://localhost:2024/"):
    """
    Send a question to the Gradio agent and return the result as a Pandas DataFrame.
    Parameters:
        question (str): The question to ask.
        server_URL (str): The URL of the Gradio server. Defaults to localhost.
    Returns:
        pd.DataFrame or None: The resulting DataFrame, or None if conversion fails.
    """
    client = Client(server_URL)
    result = client.predict(
        message=question,
        history=[],
        architecture_dropdown="Multi-Agent Supervisor",
        model_display="GCP: gemini-2.5-flash-preview-05-20",
        include_cheatsheet=False,
        include_schema=False,
        retriever_file="cheatsheet_partition_overhaul.md",
        prompt_file="system_prompt.md",
        temperature=0.2,
        top_p=0.95,
        top_k=40,
        max_steps=25,
        pydough_tool=True,
        sql_list_tables=True,
        sql_schema=True,
        sql_query=False,
        sql_query_checker=False,
        document_kb=True,
        selected_db_display="Defog: Dealership/Dealership.sqlite",
        use_sh_query_gen=False,
        tracking_backend="Phoenix",
        experiment_name="agent-react-sql",
        api_name="/process_message"
    )
    json_data = extract_json(result)
    df = extract_dataframe(json_data)
    return result, df

if __name__ == '__main__':
    sample_question = "What is the make, model and sale price of the car with the highest sale price that was sold on the same day it went out of inventory?"
    result, df = run_question(sample_question)
    print(result)
    print(df)
    