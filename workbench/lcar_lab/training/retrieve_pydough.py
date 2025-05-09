import os
import pandas as pd
from dotenv import load_dotenv
import argparse
from r2r import R2RClient
from typing import Dict, List, Optional, Tuple

# Load environment variables from root .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

def initialize_r2r_client() -> R2RClient:
    """Initialize the R2R client using the API key from .env."""
    api_key = os.getenv('R2R_API_KEY')
    if not api_key:
        raise ValueError("R2R_API_KEY not found in .env file")
    return R2RClient()

def extract_key_terms_from_code(code: str) -> List[str]:
    """Extract key Pydough-specific terms and syntax from code."""
    terms = []
    
    # Pydough-specific functions and methods
    pydough_functions = [
        'CALCULATE', 'WHERE', 'ORDER_BY', 'TOP_K', 'PARTITION',
        'HAS', 'HASNOT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'NDISTINCT',
        'ASC', 'DESC', 'JOIN_STRINGS', 'YEAR', 'MONTH'
    ]
    
    # Extract Pydough function calls
    for func in pydough_functions:
        if func in code:
            terms.append(func)
    
    # Extract collection names (they appear before dots)
    lines = code.split('\n')
    for line in lines:
        # Look for collection access patterns (e.g., "collection.subcollection")
        parts = line.split('.')
        if len(parts) > 1:
            # The first part before the dot is often a collection name
            collection = parts[0].strip()
            if collection and not collection.startswith((' ', '\t', '#')):
                terms.append(collection)
    
    # Extract aggregation patterns
    aggregation_patterns = [
        'SUM(', 'COUNT(', 'AVG(', 'MIN(', 'MAX(', 'NDISTINCT(',
        'HAS(', 'HASNOT('
    ]
    for pattern in aggregation_patterns:
        if pattern in code:
            terms.append(pattern[:-1])  # Remove the '('
    
    # Extract sorting patterns
    if 'ASC(' in code or 'DESC(' in code:
        terms.append('SORTING')
    
    # Extract partitioning patterns
    if 'PARTITION(' in code:
        terms.append('PARTITION')
    
    # Extract calculation patterns
    if '.CALCULATE(' in code:
        terms.append('CALCULATE')
    
    return list(set(terms))  # Remove duplicates

def create_rag_prompt(question: str, code: str, key_terms: List[str]) -> str:
    """Create a prompt for RAG that focuses on documentation."""
    return f"""
    Please provide documentation and explanation for the following Pydough code:
    
    Original User Question:
    {question}
    
    Pydough Generated Code Answering the User Question:
    {code}
    
    Based on information on the provided document only, focus on explaining:
    1. The Pydough-specific functions and patterns used
    2. The data flow and transformations
    3. Any important Pydough best practices demonstrated
    4. How this code follows Pydough conventions
    5. How the code addresses the original question
    6. Include key examples from the search when available. 
    7. Include key code blocks, key descriptions and definitions in your response, verbatim from source if possible.
    8. Don't make up any information or code.
    
    Key terms to consider: {', '.join(key_terms)}
    """

def perform_rag_retrieval(
    client: R2RClient,
    prompt: str,
    search_settings: Optional[Dict] = None
) -> Tuple[str, Dict]:
    """
    Perform RAG retrieval and return the generated answer and full results.
    
    Args:
        client: Initialized R2R client
        prompt: The prompt for RAG
        search_settings: Optional custom search settings
    
    Returns:
        Tuple containing:
        - generated_answer: The generated documentation
        - full_results: The complete RAG results dictionary
    """
    default_settings = {
        "filters": {"document_id": {"$eq": "4376f3de-092f-5691-84d5-66c8bb3ba69c"}},
        "search_mode": "advanced",
        "graph_settings": {"enabled": True},
        "search_strategy": "rag_fusion",
        "use_hybrid_search": True,
        "hybrid_settings": {
            "full_text_weight": 1.0,
            "semantic_weight": 5.0,
            "full_text_limit": 200,
            "rrf_k": 50
        },
        "limit": 20
    }
    
    # Merge custom settings with defaults
    settings = {**default_settings, **(search_settings or {})}
    
    try:
        rag_response = client.retrieval.rag(
            query=prompt,
            search_settings=settings
        )
        return rag_response.results.generated_answer, rag_response.results.__dict__
    except Exception as e:
        raise Exception(f"Error during RAG retrieval: {str(e)}")

def process_pydough_corpus(
    csv_path: str,
    num_examples: int = 3,
    output_md: str = 'pydough_retrieval_results.md'
) -> None:
    """Process the Pydough corpus and perform RAG retrieval for each example."""
    # Initialize R2R client
    client = initialize_r2r_client()
    
    # Load the corpus
    df = pd.read_csv(csv_path)
    df = df[df['valid'] == 'Y']  # Filter valid examples
    
    # Create markdown content
    md_content = ["# Pydough Code Documentation Retrieval Results\n"]
    
    # Process specified number of examples
    for idx, row in df.head(num_examples).iterrows():
        code = row['output']
        key_terms = extract_key_terms_from_code(code)
        
        # Add example header
        md_content.append(f"\n## Example {idx + 1}\n")
        
        # Add question
        md_content.append("### Question")
        md_content.append(f"```\n{row['question']}\n```\n")
        
        # Add Pydough code
        md_content.append("### Pydough Code")
        md_content.append("```python")
        md_content.append(code)
        md_content.append("```\n")
        
        # Add key terms
        md_content.append("### Extracted Key Terms")
        md_content.append(", ".join(key_terms) + "\n")
        
        # Add retrieval results
        md_content.append("### Documentation Retrieval Results\n")
        
        try:
            # Create prompt and perform RAG
            prompt = create_rag_prompt(row['question'], code, key_terms)
            generated_answer, full_results = perform_rag_retrieval(client, prompt)
            
            # Store RAG response in a .txt file
            response_filename = f"rag_response_example_{idx + 1}.txt"
            with open(response_filename, 'w', encoding='utf-8') as f:
                f.write(f"RAG Response for Example {idx + 1}\n")
                f.write("=" * 50 + "\n\n")
                f.write("Full RAG Results Dictionary:\n")
                f.write(str(full_results) + "\n")
            
            # Add RAG response to markdown
            md_content.append("#### Generated Documentation")
            md_content.append(generated_answer)
            
            # Add full results to markdown
            md_content.append("\n#### Full RAG Results")
            md_content.append("```json")
            md_content.append(str(full_results))
            md_content.append("```\n")
            
        except Exception as e:
            md_content.append(f"Error during RAG retrieval: {str(e)}\n")
    
    # Write markdown content to file
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))
    
    print(f"Results written to {output_md}")

def main():
    parser = argparse.ArgumentParser(description='Process Pydough corpus and perform RAG retrieval')
    parser.add_argument('--csv_path', type=str, required=True, help='Path to the CSV file containing Pydough examples')
    parser.add_argument('--num_examples', type=int, default=3, help='Number of examples to process')
    parser.add_argument('--output_md', type=str, default='pydough_retrieval_results.md', help='Output markdown file path')
    
    args = parser.parse_args()
    process_pydough_corpus(args.csv_path, args.num_examples, args.output_md)

if __name__ == '__main__':
    main() 