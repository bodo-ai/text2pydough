#!/usr/bin/env python3 
# -*- coding: utf-8 -*-

"""
PyDough Query Processor

This script processes natural language queries using the Gemini 2.5 Pro LLM
to generate and execute PyDough code for a stock broker database.
"""

import csv
import os
import re
import json
import time
import pandas as pd
import subprocess
import argparse
from datetime import datetime
from tqdm import tqdm
from typing import Optional, List

# Make sure llm package and pydantic are installed
try:
    import llm
    from pydantic import BaseModel
except ImportError:
    print("Installing required packages...")
    subprocess.run(["pip", "install", "llm", "llm-gemini", "pandas", "tqdm", "pydantic"], check=True)
    import llm
    from pydantic import BaseModel

# Define Pydantic model for structured LLM output
class PyDoughResponse(BaseModel):
    """Structured response from LLM."""
    code: str
    explanation: Optional[str] = None

# Define a Pydantic model for domain detection
class DomainDetection(BaseModel):
    """Structured response for domain detection."""
    domain: str
    confidence: float = 1.0
    reasoning: Optional[str] = None

# Domain configuration data
DOMAINS = {
    "Broker": {
        "keywords": ["customer", "ticker", "transaction", "stock", "price", "share", "trade", "broker", "exchange"],
        "metadata_file": "data/Broker_graph.json",
        "database_file": "data/Broker.db"
    },
    "Dealership": {
        "keywords": ["car", "make", "model", "salesperson", "customer", "sale", "dealership", "inventory", "vehicle", "vin"],
        "metadata_file": "data/Dealership_graph.json",
        "database_file": "data/Dealership.db"
    },
    "DermTreatment": {
        "keywords": ["doctor", "patient", "drug", "treatment", "diagnosis", "dermatology", "medical", "clinic", "adverse", "derm"],
        "metadata_file": "data/DermTreatment_graph.json",
        "database_file": "data/DermTreatment.db"
    },
    "Ewallet": {
        "keywords": ["user", "transaction", "merchant", "wallet", "balance", "payment", "coupon", "ewallet", "digital", "finance"],
        "metadata_file": "data/Ewallet_graph.json",
        "database_file": "data/Ewallet.db"
    },
    "TPCH": {
        "keywords": ["supplier", "order", "lineitem", "customer", "nation", "region", "part", "partsupp", "tpch"],
        "metadata_file": "data/tpch_demo_graph.json",
        "database_file": "data/tpch.db"
    }
    # Can add more domains as needed
}

def check_requirements():
    """Check that all required files and dependencies are available."""
    print("\n--- Checking Requirements ---")
    
    # Check required files
    required_files = ['queries.csv', 'cheatsheet.md', 'defog_broker.md', 'data/Broker_graph.json', 'data/Broker.db']
    missing_files = []

    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
            
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        print("Please ensure these files are present in the correct locations.")
        return False
    else:
        print("✅ All required files found")
    
    # Configure gemini-2.5-pro-preview-05-06 model
    try:
        model = llm.get_model("gemini-2.5-pro-preview-05-06")
        print("✅ Successfully loaded Gemini model")
    except Exception as e:
        print(f"❌ Error loading Gemini model: {str(e)}")
        print("Make sure you've set your API key with: llm keys set gemini")
        return False
    
    return True

def get_queries(category=None):
    """
    Read queries.csv and optionally filter by category.
    Returns all queries if category is None, or only queries matching the specified category.
    """
    all_queries = []
    categories = set()
    category_queries = {}
    
    try:
        # Try multiple encodings to handle potential issues
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1']:
            try:
                with open('queries.csv', 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    fieldnames = reader.fieldnames
                    if not fieldnames:
                        continue
                        
                    # Check for Category column with case insensitivity
                    category_col = None
                    for col in fieldnames:
                        if col.lower() == 'category':
                            category_col = col
                            break
                    
                    if not category_col:
                        continue
                        
                    # Reset file pointer and read rows
                    f.seek(0)
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    
                    # Process all rows
                    for row in rows:
                        cat = row[category_col]
                        query = row.get('Query')
                        if not query:
                            continue
                            
                        # Store in overall list
                        all_queries.append(query)
                        
                        # Track categories and queries by category
                        categories.add(cat)
                        if cat not in category_queries:
                            category_queries[cat] = []
                        category_queries[cat].append(query)
                    
                    # If we got here with data, we succeeded
                    if all_queries:
                        break
            except Exception as inner_e:
                print(f"Attempt with {encoding} encoding failed: {str(inner_e)}")
                continue
        
        # If specific category requested, return just those queries
        if category:
            result = category_queries.get(category, [])
            print(f"Found {len(result)} queries for category '{category}'")
            return result
        
        # Otherwise return all queries
        print(f"Found {len(all_queries)} queries across {len(categories)} categories")
        print(f"Categories: {', '.join(sorted(categories))}")
        return all_queries
        
    except Exception as e:
        print(f"❌ Error reading queries.csv: {str(e)}")
        return []

def read_file_content(file_path):
    """Read the content of a file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error reading {file_path}: {str(e)}")
        return ""

def keyword_based_detect_domain(query_text):
    """
    Detect the domain/database schema using keyword matching.
    This is a fallback method used when LLM detection fails.
    Returns a tuple of (domain_name, metadata_file, database_file)
    """
    # Convert query to lowercase for case-insensitive matching
    query_lower = query_text.lower()
    
    # Count occurrences of keywords for each domain
    domain_scores = {}
    for domain, config in DOMAINS.items():
        score = 0
        for keyword in config["keywords"]:
            if keyword.lower() in query_lower:
                score += 1
        domain_scores[domain] = score
    
    # Get domain with highest score, default to Broker if no matches
    if not domain_scores or max(domain_scores.values()) == 0:
        print("⚠️ Could not detect domain from query, defaulting to Broker")
        selected_domain = "Broker"
    else:
        selected_domain = max(domain_scores.items(), key=lambda x: x[1])[0]
    
    # Get metadata and database files for selected domain
    selected_config = DOMAINS[selected_domain]
    
    print(f"🔍 Detected domain (keyword-based): {selected_domain}")
    return (
        selected_domain,
        selected_config["metadata_file"],
        selected_config["database_file"]
    )

def detect_domain_with_llm(query_text):
    """
    Detect domain using LLM with structured output.
    Returns a tuple of (domain_name, metadata_file, database_file)
    """
    try:
        # Use gemini-2.0-flash for efficient domain detection
        model = llm.get_model("gemini-2.0-flash")
        
        # Build domain list for prompt
        domain_list = "\n".join([f"{i+1}. {domain} - {', '.join(config['keywords'][:5])}" 
                              for i, (domain, config) in enumerate(DOMAINS.items())])
        
        prompt = f"""
Identify which database domain this query is asking about:
"{query_text}"

Available domains:
{domain_list}

Return the domain name that best matches the query.
"""
        # Get structured response
        response = model.prompt(prompt, schema=DomainDetection)
        data = json.loads(response.text())
        
        detected_domain = data["domain"]
        confidence = data.get("confidence", 0.0)
        reasoning = data.get("reasoning", "")
        
        # Check if detected domain exists in our configuration
        if detected_domain in DOMAINS:
            print(f"🔍 Detected domain (LLM): {detected_domain} (confidence: {confidence:.2f})")
            if reasoning:
                print(f"   Reasoning: {reasoning}")
                
            return (
                detected_domain,
                DOMAINS[detected_domain]["metadata_file"],
                DOMAINS[detected_domain]["database_file"]
            )
        else:
            print(f"⚠️ LLM detected unknown domain: '{detected_domain}', falling back to keyword matching")
            return keyword_based_detect_domain(query_text)
            
    except Exception as e:
        print(f"⚠️ LLM domain detection failed: {str(e)}, falling back to keyword matching")
        return keyword_based_detect_domain(query_text)

def detect_domain(query_text):
    """
    Main domain detection function that tries LLM first, then falls back to keyword matching.
    Returns a tuple of (domain_name, metadata_file, database_file)
    """
    return detect_domain_with_llm(query_text)

def create_prompt(query, cheatsheet_content, schema_content, domain_name="Broker"):
    """Create a prompt for the LLM with examples."""
    prompt = f"""
# Task: Convert a natural language query into PyDough code for a {domain_name} database

# User Query
{query}

# {domain_name} Schema Information
{schema_content}

# PyDough Cheatsheet
{cheatsheet_content}

# Example 1: List all records from main collection
```python
result = {domain_name}.{domain_name if domain_name == "Broker" else "Customer"}.CALCULATE(
    *  # Select all fields
)
```

# Example 2: Filter records by a condition
```python
result = {domain_name}.{domain_name if domain_name == "Broker" else "Orders"}.WHERE(
    /* condition goes here */
).CALCULATE(
    *  # Select needed fields
)
```

# Your task:
Given the user query, schema information, and PyDough cheatsheet above, create PyDough code that correctly answers the query.
Return ONLY Python code that produces the correct result as a variable named 'result'.
DON'T include any explanations or comments - just provide the working PyDough code.
"""
    return prompt

def extract_pydough_code(response):
    """
    Extract PyDough code from LLM response.
    This function is kept for backward compatibility but is no longer used
    when structured output (schema parameter) is in use.
    """
    # Look for Python code blocks in the response
    pattern = r'```(?:python)?\s*([\s\S]*?)\s*```'
    matches = re.findall(pattern, str(response))
    
    if matches:
        code = matches[0].strip()
        # Ensure the code assigns to a variable named 'result'
        if not re.search(r'\bresult\s*=', code):
            # If not found, wrap the code with result assignment
            if code.startswith('return '):
                code = code.replace('return ', 'result = ', 1)
            else:
                code = f"result = {code}"
        return code
    
    # Fallback: If no code block found, look for any Python-like code
    code_like_pattern = r'result\s*=\s*[^;]+'
    matches = re.findall(code_like_pattern, str(response))
    if matches:
        return matches[0].strip()
    
    return None

def review_code_with_llm(code, model=None):
    """Send the generated code to LLM for review and improvement."""
    if model is None:
        model = llm.get_model("gemini-2.5-pro-preview-05-06")
    
    # Define a Pydantic model for code review response
    class CodeReviewResponse(BaseModel):
        reviewed_code: str
    
    prompt = f"""
Review and improve this PyDough code to ensure it is syntactically correct and follows best practices.
Fix any potential issues and return only the corrected code.

```python
{code}
```

Ensure the code:
1. Uses proper PyDough syntax
2. Has correct property and collection references
3. Assigns the final result to a variable named 'result'
4. Has no syntax errors
"""
    
    print("⏳ Sending code to LLM for review and improvement...")
    try:
        # Use schema parameter for structured output
        response = model.prompt(prompt, schema=CodeReviewResponse)
        review_data = json.loads(response.text())
        clean_response = review_data["reviewed_code"]
        
        # Ensure result assignment
        if not re.search(r'\bresult\s*=', clean_response):
            if clean_response.startswith('return '):
                clean_response = clean_response.replace('return ', 'result = ', 1)
            else:
                clean_response = f"result = {clean_response}"
        
        print("✅ Code review complete")
        return clean_response
    except Exception as e:
        # Fallback to regex extraction if structured output fails
        print(f"⚠️ Structured output failed for code review: {str(e)}")
        print("Falling back to regex extraction...")
        response_text = str(model.prompt(prompt))
        return extract_pydough_code(response_text) or code

def adapt_and_execute_code(pydough_code, output_file_name, domain_info=None):
    """Adapt and execute the PyDough code."""
    
    # If domain_info not provided, use default Broker
    if domain_info is None:
        domain_name = "Broker"
        metadata_file = "data/Broker_graph.json"
        database_file = "data/Broker.db"
    else:
        domain_name, metadata_file, database_file = domain_info
    
    # Ensure results directory exists
    os.makedirs("results", exist_ok=True)
    
    # Construct the full path for the output file inside the results directory
    output_file_path = os.path.join("results", output_file_name)

    # Create a modified version of test.py with the new pydough code
    adapted_code = f"""
import pydough
from pydough import init_pydough_context

# Load metadata and connect to database
pydough.active_session.load_metadata_graph("{metadata_file}", "{domain_name}")
pydough.active_session.connect_database("sqlite", database="{database_file}")

@init_pydough_context(pydough.active_session.metadata)
def func():
    # Generated PyDough code
    {pydough_code}
    return result

result = func()
print("\\nSQL Query:")
print(pydough.to_sql(result))
print("\\nResult:")
print(pydough.to_df(result).head(10))  # Show only first 10 rows
"""

    # Write to Python file in the results directory
    with open(output_file_path, 'w') as f:
        f.write(adapted_code)
    
    print(f"✅ Generated PyDough code written to {output_file_path}")
    
    return adapted_code, output_file_path # Return the full path

def execute_pydough_script(script_path):
    """Execute the generated Python file and capture output."""
    try:
        print(f"⏳ Executing {script_path}...")
        print(f"Command: python {script_path}")
        
        # Use Popen for more control and to read output in real-time if needed
        process = subprocess.Popen(
            ["python", script_path], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=60)  # Timeout after 60 seconds
        
        if process.returncode == 0:
            print(f"✅ Execution successful")
            print("\nOutput:")
            print(stdout)
            return {'success': True, 'output': stdout}
        else:
            print(f"❌ Execution failed with return code {process.returncode}")
            print("Error:")
            print(stderr)
            
            if stdout:
                print("\nPartial output before error:")
                print(stdout)
                
            return {
                'success': False, 
                'error': stderr,
                'partial_output': stdout if stdout else None,
                'returncode': process.returncode
            }
            
    except subprocess.TimeoutExpired:
        process.kill() # Ensure process is killed on timeout
        stdout, stderr = process.communicate()
        print("❌ Execution timed out after 60 seconds")
        return {
            'success': False, 
            'error': 'Execution timed out after 60 seconds',
            'partial_output': stdout.strip() if stdout else None,
            'partial_error': stderr.strip() if stderr else None
        }
    except FileNotFoundError:
        error_msg = f"❌ Python interpreter not found or script file {script_path} doesn't exist"
        print(error_msg)
        return {'success': False, 'error': error_msg}
    except Exception as e:
        error_msg = f"❌ Error executing script: {str(e)}"
        print(error_msg)
        return {'success': False, 'error': error_msg}

# Helper function to save execution artifacts
def save_execution_artifacts(execution_result, base_filename):
    """Saves execution output (stdout, stderr, SQL) to files."""
    os.makedirs("results", exist_ok=True)

    if not execution_result:
        print("ℹ️ No execution result to save.")
        return

    # Save SQL query and full output if execution was successful
    if execution_result.get("success") and "output" in execution_result:
        output = execution_result["output"]
        
        # Try to extract SQL query
        sql_match = re.search(r'SQL Query:\s*\n(.*?)(?:\n\nResult:|\Z)', output, re.DOTALL)
        if sql_match:
            sql_query = sql_match.group(1).strip()
            sql_file_path = os.path.join("results", f"sql_{base_filename}.sql")
            with open(sql_file_path, 'w') as f:
                f.write(sql_query)
            print(f"💾 SQL query saved to {sql_file_path}")
        
        # Save full output
        output_text_file_path = os.path.join("results", f"output_{base_filename}.txt")
        with open(output_text_file_path, 'w') as f:
            f.write(output)
        print(f"💾 Execution output saved to {output_text_file_path}")
    
    # If execution failed, save error
    elif "error" in execution_result:
        error_message = execution_result["error"]
        if execution_result.get("partial_output"):
            error_message += "\n\n--- Partial Output Before Error ---\n" + execution_result["partial_output"]
        
        error_file_path = os.path.join("results", f"error_{base_filename}.txt")
        with open(error_file_path, 'w') as f:
            f.write(error_message)
        print(f"💾 Execution error saved to {error_file_path}")
    else:
        print("ℹ️ Execution result present, but no standard output or error field to save.")

def process_query(query_text, execute=False, save_results=True, model=None, use_code_review=False, domain=None):
    """Process a single query through the LLM."""
    print(f"\nProcessing query: {query_text}")
    print("-" * 80)
    
    # If model not provided, get it
    if model is None:
        model = llm.get_model("gemini-2.5-pro-preview-05-06")
    
    result_data = {
        "query": query_text,
        "timestamp": datetime.now().isoformat(),
        "execution": None,
        "domain": "Unknown" # Default domain
    }
    
    adapted_code_content = None 
    domain_name = "Unknown" # Initialize domain_name
    
    try:
        # Detect domain if not explicitly provided
        if domain is None:
            domain_info = detect_domain(query_text)
        else:
            # Use specified domain if it exists in DOMAINS
            if domain in DOMAINS:
                domain_info = (domain, DOMAINS[domain]["metadata_file"], DOMAINS[domain]["database_file"])
            else:
                raise ValueError(f"Unknown domain: {domain}")
                
        domain_name, metadata_file, database_file = domain_info
        result_data["domain"] = domain_name
        
        # Read cheatsheet
        cheatsheet_content = read_file_content('cheatsheet.md')
        
        # Read domain-specific schema information
        schema_file = f"defog_{domain_name.lower()}.md"
        if os.path.exists(schema_file):
            schema_content = read_file_content(schema_file)
        else:
            # Fallback to broker schema if the domain-specific one is not found
            schema_content = read_file_content('defog_broker.md')
            print(f"⚠️ Could not find schema file {schema_file}, using fallback")
            if not schema_content:
                print(f"⚠️ Using a generic description for {domain_name}")
                schema_content = f"# {domain_name} Database\nThis database contains information related to {domain_name}."
        
        # Create the prompt with domain-specific schema
        prompt = create_prompt(query_text, cheatsheet_content, schema_content, domain_name)
        
        # Send to LLM and get structured response using schema parameter
        print("⏳ Sending query to Gemini...")
        try:
            # Try to get structured output using PyDoughResponse schema
            response = model.prompt(prompt, schema=PyDoughResponse)
            response_data = json.loads(response.text())
            pydough_code = response_data["code"]
            explanation = response_data.get("explanation", "")
            
            # Store the raw response text for debugging
            result_data["llm_response"] = f"Structured response: {response.text()}"
            if explanation:
                result_data["explanation"] = explanation
                
            print("✅ Received structured response from LLM")
        except Exception as e:
            # Fallback to unstructured response if schema fails
            print(f"⚠️ Structured output failed: {str(e)}")
            print("Falling back to regex extraction...")
            response = model.prompt(prompt)
            result_data["llm_response"] = str(response)
            
            # Print the full response
            print("\n🤖 LLM Response:")
            print(response)
            
            # Extract PyDough code using regex
            pydough_code = extract_pydough_code(str(response))
        
        result_data["pydough_code"] = pydough_code
        
        if pydough_code:
            print("\n📄 Generated PyDough Code:")
            print(pydough_code)
            
            # Run code review if enabled
            if use_code_review:
                reviewed_code = review_code_with_llm(pydough_code, model)
                if reviewed_code and reviewed_code != pydough_code:
                    print("\n📝 Improved PyDough Code after Review:")
                    print(reviewed_code)
                    pydough_code = reviewed_code
                    result_data["reviewed_code"] = reviewed_code
            
            # Create a unique filename for this query
            safe_query = re.sub(r'[^\w]', '_', query_text[:20]).strip('_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file_name = f"{domain_name.lower()}_query_{safe_query}_{timestamp}.py"
            
            # Adapt the code and get the full path to the file
            print("\n🔄 Adapting code for execution")
            adapted_code_content, output_file_path = adapt_and_execute_code(pydough_code, output_file_name, domain_info)
            result_data["adapted_code"] = adapted_code_content
            result_data["output_file"] = output_file_path 
            
            # Execute if requested
            if execute:
                execution_result = execute_pydough_script(output_file_path)
                result_data["execution"] = execution_result
        else:
            print("\n❌ No PyDough code found in the response")
    
    except Exception as e:
        print(f"\n❌ Error processing query: {str(e)}")
        result_data["error"] = str(e)
    
    # Save results if requested
    if save_results:
        os.makedirs("results", exist_ok=True)
        
        safe_query = re.sub(r'[^\w]', '_', query_text[:20]).strip('_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Ensure domain_name is defined for base_filename, even if detection failed early
        current_domain_name = result_data.get("domain", "unknown_domain") 
        base_filename = f"{current_domain_name.lower()}_{safe_query}_{timestamp}"
        
        # Save comprehensive JSON results
        result_file_path = os.path.join("results", f"query_result_{base_filename}.json")
        with open(result_file_path, 'w') as f:
            json.dump(result_data, f, indent=2)
        print(f"\n💾 JSON results saved to {result_file_path}")
        
        # Save execution artifacts using the helper function
        if execute and "execution" in result_data:
            save_execution_artifacts(result_data["execution"], base_filename)
        
        if result_data.get("output_file") and os.path.exists(result_data.get("output_file")):
             print(f"ℹ️ Generated Python code is at {result_data['output_file']}")
        elif result_data.get("adapted_code"):
             print(f"⚠️ Generated Python code was created but not found at the expected path: {result_data.get('output_file')}")

    return result_data

def process_all_queries(queries, max_queries=None, execute=False, save_results=True, use_code_review=False, domain=None):
    """Process multiple queries."""
    results = []
    summary = {
        "total": 0,
        "successful_generation": 0,
        "successful_execution": 0,
        "failed": 0
    }
    
    if max_queries is not None:
        queries = queries[:max_queries]
    
    # Get the model once for all queries
    model = llm.get_model("gemini-2.5-pro-preview-05-06")
    
    print(f"⏳ Processing {len(queries)} queries...")
    
    for i, query in enumerate(tqdm(queries)):
        print(f"\n--- Query {i+1}/{len(queries)} ---")
        result = process_query(query, execute=execute, save_results=save_results, model=model, use_code_review=use_code_review, domain=domain)
        results.append(result)
        
        # Update summary statistics
        summary["total"] += 1
        if "pydough_code" in result and result["pydough_code"]:
            summary["successful_generation"] += 1
        else:
            summary["failed"] += 1
            
        if "execution" in result and result["execution"] and result["execution"].get("success", False):
            summary["successful_execution"] += 1
    
    # Print summary
    print("\n=== Processing Summary ===")
    print(f"Total queries processed: {summary['total']}")
    print(f"Successful code generation: {summary['successful_generation']} ({summary['successful_generation']/summary['total']*100:.1f}%)")
    
    if execute:
        print(f"Successful code execution: {summary['successful_execution']} ({summary['successful_execution']/summary['total']*100:.1f}%)")
    
    print(f"Failed queries: {summary['failed']} ({summary['failed']/summary['total']*100:.1f}%)")
    
    # Save summary if requested
    if save_results:
        os.makedirs("results", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = f"results/processing_summary_{timestamp}.json"
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\n💾 Summary saved to {summary_file}")
    
    return results, summary

def interactive_mode():
    """Run the program in interactive mode."""
    print("\n=== PyDough Query Processor - Interactive Mode ===")
    
    # Check requirements
    if not check_requirements():
        return
    
    # Get all queries and categorize them
    all_queries = {}
    categories = []
    
    # Try to read all categories of queries
    for domain in DOMAINS.keys():
        domain_queries = get_queries(domain)
        if domain_queries:
            all_queries[domain] = domain_queries
            categories.append(domain)
    
    if not categories:
        print("No queries found in any category. Exiting.")
        return
    
    print(f"\nFound queries for the following categories: {', '.join(categories)}")
    
    # Global settings
    use_code_review = False
    domain = None  # Auto-detect by default
    
    while True:
        domain_status = f"Auto-detect (current: {domain})" if domain else "Auto-detect"
        
        print("\n=== Menu ===")
        print("1. Process a specific query by category")
        print("2. Process a custom query")
        print("3. Process multiple queries in batch")
        print("4. List all queries by category")
        print("5. Toggle LLM code review (Currently: " + ("ON" if use_code_review else "OFF") + ")")
        print(f"6. Set database domain (Currently: {domain_status})")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ")
        
        if choice == "1":
            # First select a category
            print("\nAvailable categories:")
            for i, category in enumerate(categories):
                print(f"{i+1}. {category} ({len(all_queries[category])} queries)")
            
            try:
                category_index = int(input("\nEnter the number of the category (or 0 to cancel): ")) - 1
                if 0 <= category_index < len(categories):
                    selected_category = categories[category_index]
                    category_queries = all_queries[selected_category]
                    
                    # Then select a query within that category
                    print(f"\nQueries for {selected_category}:")
                    for i, query in enumerate(category_queries):
                        print(f"{i+1}. {query}")
                    
                    query_index = int(input("\nEnter the number of the query you want to process (or 0 to cancel): ")) - 1
                    if 0 <= query_index < len(category_queries):
                        selected_query = category_queries[query_index]
                        should_execute = input("Execute the generated code? (y/n): ").lower() == 'y'
                        # Use the selected category as domain hint if auto-detect is not enabled
                        current_domain = selected_category if domain else None
                        process_query(selected_query, execute=should_execute, use_code_review=use_code_review, domain=current_domain)
                    else:
                        print("No query selected or invalid query number")
                else:
                    print("No category selected or invalid category number")
            except ValueError:
                print("Invalid input. Please enter a number.")
                
        elif choice == "2":
            custom_query = input("\nEnter your custom query about any supported database: ")
            if custom_query:
                should_execute = input("Execute the generated code? (y/n): ").lower() == 'y'
                process_query(custom_query, execute=should_execute, use_code_review=use_code_review, domain=domain)
            else:
                print("No query entered")
                
        elif choice == "3":
            # First, select a category
            print("\nSelect a category for batch processing:")
            print("0. All categories")
            for i, category in enumerate(categories):
                print(f"{i+1}. {category} ({len(all_queries[category])} queries)")
                
            try:
                category_index = int(input("\nEnter the number of the category (0 for all): "))
                if 0 <= category_index <= len(categories):
                    # Determine which queries to process
                    if category_index == 0:
                        # All queries
                        queries_to_process = []
                        for cat in categories:
                            queries_to_process.extend(all_queries[cat])
                        batch_category = None  # No specific category hint for auto-detect
                    else:
                        # Specific category
                        selected_category = categories[category_index-1]
                        queries_to_process = all_queries[selected_category]
                        batch_category = selected_category  # Use the selected category as a hint if auto-detect is not enabled
                    
                    max_queries = int(input(f"\nHow many queries to process (max {len(queries_to_process)})? Enter 0 for all: "))
                    if max_queries == 0:
                        max_queries = None
                        
                    should_execute = input("Execute the generated code for each query? (y/n): ").lower() == 'y'
                    
                    # Override batch category with selected domain if auto-detect is not enabled
                    final_domain = domain if domain else batch_category
                    
                    # Process the queries
                    results, summary = process_all_queries(
                        queries_to_process, 
                        max_queries=max_queries, 
                        execute=should_execute,
                        use_code_review=use_code_review,
                        domain=final_domain
                    )
                else:
                    print("Invalid category selection")
            except ValueError:
                print("Invalid input. Please enter a number.")
                
        elif choice == "4":
            print("\nAll queries by category:")
            for category in categories:
                print(f"\n--- {category} ({len(all_queries[category])} queries) ---")
                for i, query in enumerate(all_queries[category]):
                    print(f"{i+1}. {query}")
                
        elif choice == "5":
            use_code_review = not use_code_review
            status = "enabled" if use_code_review else "disabled"
            print(f"\nLLM code review is now {status}")
                
        elif choice == "6":
            print("\nAvailable domains:")
            print("1. Auto-detect (default)")
            for i, available_domain in enumerate(sorted(DOMAINS.keys())):
                print(f"{i+2}. {available_domain}")
            
            domain_choice = input(f"\nEnter domain choice (1-{len(DOMAINS)+1}): ")
            try:
                choice_num = int(domain_choice)
                if choice_num == 1:
                    domain = None
                    print("Domain set to Auto-detect")
                elif 2 <= choice_num <= len(DOMAINS)+1:
                    domain = sorted(DOMAINS.keys())[choice_num-2]
                    print(f"Domain set to {domain}")
                else:
                    print("Invalid choice, keeping current setting")
            except ValueError:
                print("Invalid input, keeping current setting")
                
        elif choice == "7":
            print("\nExiting...")
            break
            
        else:
            print("Invalid choice. Please enter a number between 1 and 7.")

def main():
    """Main function to parse arguments and run the program."""
    parser = argparse.ArgumentParser(description='Process PyDough queries using LLM')
    parser.add_argument('--query', '-q', type=str, help='A specific query to process')
    parser.add_argument('--category', '-c', type=str, help='Process queries from a specific category')
    parser.add_argument('--batch', '-b', type=int, help='Process the first N queries in batch mode')
    parser.add_argument('--execute', '-e', action='store_true', help='Execute the generated PyDough code')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--review', action='store_true', help='Enable LLM code review (disabled by default)')
    parser.add_argument('--domain', '-d', type=str, choices=['auto'] + list(DOMAINS.keys()), 
                      default='auto', help='Specify database domain to use')
    parser.add_argument('--run-file', '-r', type=str, help='Execute an existing PyDough Python file (e.g., results/code_query.py)')
    parser.add_argument('--list-categories', '-l', action='store_true', help='List all available query categories')
    
    args = parser.parse_args()
    
    # List categories and exit if requested
    if args.list_categories:
        # Read queries.csv to find all categories
        all_queries = {}
        for domain in DOMAINS.keys():
            domain_queries = get_queries(domain)
            if domain_queries:
                all_queries[domain] = domain_queries
        
        if all_queries:
            print("\nAvailable Categories:")
            for category, queries in all_queries.items():
                print(f"- {category}: {len(queries)} queries")
        else:
            print("No query categories found.")
        return
    
    # If run-file is specified, just execute that file
    if args.run_file:
        if os.path.exists(args.run_file):
            print(f"Executing existing file: {args.run_file}")
            execution_result = execute_pydough_script(args.run_file)
            
            # Determine a base filename from the input file path for saving artifacts
            try:
                base_filename_from_path = os.path.basename(args.run_file).replace('.py', '')
                # Prefix with 'runfile_' to distinguish from normal processing results if not already clear
                if not any(base_filename_from_path.startswith(f"{domain.lower()}_query_") for domain in DOMAINS.keys()):
                    base_filename = f"runfile_{base_filename_from_path}" 
                else:
                    base_filename = base_filename_from_path
                save_execution_artifacts(execution_result, base_filename)
            except Exception as e:
                print(f"Error preparing to save results from run-file: {str(e)}")
            return
        else:
            print(f"Error: File {args.run_file} does not exist")
            return
    
    # Check requirements first
    if not check_requirements():
        return
    
    # Determine if code review should be used
    use_code_review = args.review
    
    # Determine domain
    domain_arg = None  # Default to auto-detect for process_query/process_all_queries
    if args.domain != 'auto':
        domain_arg = args.domain
    
    # Handle different modes
    if args.interactive:
        interactive_mode() # interactive_mode handles its own domain logic
    elif args.query:
        process_query(args.query, execute=args.execute, use_code_review=use_code_review, domain=domain_arg)
    elif args.category:
        # Process queries from a specific category
        category_queries = get_queries(args.category)
        if category_queries:
            if args.batch:
                batch_size = min(args.batch, len(category_queries))
                queries_to_process = category_queries[:batch_size]
            else:
                queries_to_process = category_queries
                
            process_all_queries(
                queries_to_process, 
                execute=args.execute, 
                use_code_review=use_code_review,
                domain=domain_arg or args.category # Use category as domain hint if auto-detect is enabled
            )
        else:
            print(f"No queries found for category '{args.category}'. Exiting.")
    elif args.batch:
        # Without category specified, use Broker queries for backward compatibility
        broker_queries = get_queries("Broker")
        if broker_queries:
            process_all_queries(broker_queries, max_queries=args.batch, execute=args.execute, 
                              use_code_review=use_code_review, domain=domain_arg)
        else:
            print("No broker queries found. Exiting.")
    else:
        # Default to interactive mode if no arguments provided
        interactive_mode()

if __name__ == "__main__":
    main() 