"""
classify_errors.py – tag each row with an error-class label using both regex and LLM
-----------------------------------------------------------

Usage
-----
python classify_errors.py  input.csv  [output.csv]  [--limit N]
"""

from __future__ import annotations
import sys
import re
import pandas as pd
from openevals.llm import create_llm_as_judge
from langchain_google_vertexai import ChatVertexAI
from typing import Dict, List, Optional
import json
import os
from dotenv import load_dotenv
import warnings
import argparse
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
import numpy as np

# Suppress schema validation warnings from LangChain's Google Vertex AI integration
# This warning occurs because the Vertex AI client accepts additional properties
# that aren't explicitly defined in the schema, but they are valid configuration options
warnings.filterwarnings(
    "ignore",
    message="Key 'additionalProperties' is not supported in schema",
    category=UserWarning,
    module="langchain_google_vertexai"
)

# Load environment variables from .env file
load_dotenv()

###############################################################################
# 1.  Configure the patterns that identify each leaf class
###############################################################################

CLASS_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # Order matters: first match wins.
    (
        "UnknownCollectionError",
        re.compile(r"Unrecognized\s+term", re.IGNORECASE),
    ),
    (
        "UnsupportedOperatorError",
        re.compile(r"(is\s+not\s+callable|does\s+not\s+yet\s+support)", re.IGNORECASE),
    ),
    (
        "EvaluationError",
        re.compile(
            r"(only\s+execute\s+one\s+statement|invalid\s+syntax|cannot\s+execute|"
            r"sqlite|SQLSTATE|runtime\s*error)",
            re.IGNORECASE,
        ),
    ),
    (
        "RelationshipError",
        re.compile(r"ancestor", re.IGNORECASE),
    ),
    (
        "CardinalityError",
        re.compile(r"Expected\s+all\s+terms.*singular|CALCULATE", re.IGNORECASE),
    ),
    (
        "TypeSystemError",
        re.compile(
            r"Expected\s+an\s+expression,\s+but\s+received\s+a\s+collection",
            re.IGNORECASE,
        ),
    ),
    (
        "IncompatibleTypesError",
        re.compile(r"cannot\s+be\s+treated\s+as\s+a\s+boolean", re.IGNORECASE),
    ),
    (
        "CycleError",
        re.compile(r"(maximum\s+recursion\s+depth\s+exceeded|cyclic)", re.IGNORECASE),
    ),
]

DEFAULT_LABEL = "UnclassifiedError"   # fallback for unmatched rows
NO_EXCEPTION_LABEL = "NoException"    # optional label when exception cell is empty

###############################################################################
# 2.  Helper: classify a single message using regex
###############################################################################

def classify_exception(msg: str | float) -> str:
    """Return the first leaf class whose regex matches *msg*."""
    if pd.isna(msg) or msg == "":
        return NO_EXCEPTION_LABEL
    for class_name, pat in CLASS_PATTERNS:
        if pat.search(msg):
            return class_name
    return DEFAULT_LABEL

# Load the reference data
reference_df = pd.read_csv('sample_data/error_subclass_with_main_classes.csv')

# Format subclasses into a readable string
SUBCLASSES_TEXT = "\n".join([
    f"- {row['Proposed sub-class']}: {row['What it usually means & typical next step']}"
    for _, row in reference_df.iterrows()
])

# Create a prompt template for the evaluator
CLASSIFICATION_PROMPT = """You are an expert at classifying error messages into specific subclasses.
Given an error message and a list of possible subclasses with their descriptions, determine which subclass best matches the error.

Here are the possible subclasses and their descriptions:
{inputs}

Error message to classify:
{outputs}

Please respond with a JSON object containing:
1. "subclass": The name of the best matching subclass
2. "confidence": A number between 0 and 1 indicating your confidence in the classification
3. "explanation": A brief explanation of why this subclass is the best match

If none of the subclasses match well, respond with "Unknown" as the subclass and explain why.
"""

def create_evaluator():
    # Check for GCP credentials from .env
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not found in .env file")
    
    # Set the credentials path for the current process
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    
    # Create Gemini model instance
    gemini = ChatVertexAI(
        model_name="gemini-2.5-flash-preview-05-20", #"gemini-2.0-flash-001",#
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location="us-central1",
        temperature=0,
    )
    
    # Create the judge with the Gemini model
    return create_llm_as_judge(
        prompt=CLASSIFICATION_PROMPT,
        judge=gemini,
        feedback_key="error_classification"
    )

def get_main_class(subclass: str, reference_df: pd.DataFrame) -> str:
    """Get the main class for a given subclass from the reference data."""
    if subclass == 'Unknown' or subclass == 'NoException':
        return subclass
    match = reference_df[reference_df['Proposed sub-class'] == subclass]
    if len(match) > 0:
        return match.iloc[0]['Main class']
    return subclass  # Return the subclass if no main class is found

def process_exceptions(input_file: str, output_file: str, limit: Optional[int] = None):
    # Load the test execution data
    test_df = pd.read_csv(input_file)
    
    # Filter for rows with exceptions if limit is specified
    if limit is not None:
        test_df = test_df[test_df['exception'].notna() & (test_df['exception'] != '')].head(limit)
        print(f"Processing {len(test_df)} examples with exceptions...")
    
    # First, apply regex-based classification
    print("Applying regex-based classification...")
    test_df["regex_classification"] = test_df["exception"].apply(classify_exception)
    
    # Print regex classification distribution
    print("\nRegex classification distribution:")
    print(test_df["regex_classification"].value_counts())
    print()
    
    # Create the evaluator for LLM-based classification
    print("Creating LLM evaluator...")
    evaluator = create_evaluator()
    
    # Process each exception with LLM
    print("Processing exceptions with LLM...")
    results = []
    for _, row in test_df.iterrows():
        if pd.isna(row['exception']) or row['exception'].strip() == '':
            continue
            
        # Get the classification
        result = evaluator(
            inputs=SUBCLASSES_TEXT,
            outputs=row['exception']
        )
        
        # Parse the result
        try:
            # Extract classification from the comment field
            comment = result.get('comment', '')
            score = result.get('score', False)
            
            # Try to find the subclass in the comment
            subclass = 'Unknown'
            confidence = 1.0 if score else 0.0
            explanation = comment
            
            # Look for subclass mentions in the comment
            for _, ref_row in reference_df.iterrows():
                subclass_name = ref_row['Proposed sub-class']
                if subclass_name.lower() in comment.lower():
                    subclass = subclass_name
                    break
            
            results.append({
                'question': row['question'],
                'exception': row['exception'],
                'regex_classification': row['regex_classification'],
                'llm_classification': subclass,
                'confidence': confidence,
                'explanation': explanation
            })
        except Exception as e:
            print(f"Error processing row: {e}")
            print(f"Raw result: {result}")
            results.append({
                'question': row['question'],
                'exception': row['exception'],
                'regex_classification': row['regex_classification'],
                'llm_classification': 'Unknown',
                'confidence': 0.0,
                'explanation': f'Failed to process classification result: {str(e)}'
            })
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_file, index=False)
    print(f"Processed {len(results)} exceptions. Results saved to {output_file}")
    
    # Print LLM classification distribution
    print("\nLLM classification distribution:")
    print(results_df["llm_classification"].value_counts())
    print()
    
    # Convert classifications to main classes for comparison
    results_df['regex_main_class'] = results_df['regex_classification'].apply(lambda x: get_main_class(x, reference_df))
    results_df['llm_main_class'] = results_df['llm_classification'].apply(lambda x: get_main_class(x, reference_df))
    
    # Print agreement statistics at the class level
    agreement = (results_df["regex_main_class"] == results_df["llm_main_class"]).mean()
    print(f"\nClassification agreement between regex and LLM (at class level): {agreement:.2%}")
    
    # Generate classification report
    print("\nClassification Report (Regex as ground truth):")
    report = classification_report(
        results_df['regex_main_class'],
        results_df['llm_main_class'],
        output_dict=True
    )
    
    # Convert report to DataFrame for better formatting
    report_df = pd.DataFrame(report).transpose()
    report_df = report_df.round(3)  # Round to 3 decimal places
    print(report_df)
    
    # Save classification report to CSV
    report_output_file = output_file.rsplit('.', 1)[0] + '_classification_report.csv'
    report_df.to_csv(report_output_file)
    print(f"\nClassification report saved to: {report_output_file}")
    
    # Generate and save confusion matrix plot
    labels = sorted(set(results_df['regex_main_class'].unique()) | set(results_df['llm_main_class'].unique()))
    cm = confusion_matrix(
        results_df['regex_main_class'],
        results_df['llm_main_class'],
        labels=labels
    )
    
    plt.figure(figsize=(10, 8))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(cmap='Blues', values_format='d')
    plt.title('Confusion Matrix: Regex vs LLM Classification (Class Level)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    cm_output_file = output_file.rsplit('.', 1)[0] + '_confusion_matrix.png'
    plt.savefig(cm_output_file)
    print(f"Confusion matrix plot saved to: {cm_output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Classify error messages in a CSV file.')
    parser.add_argument('input_file', help='Input CSV file containing error messages')
    parser.add_argument('output_file', nargs='?', help='Output CSV file (default: classified_<input_file>)')
    parser.add_argument('--limit', type=int, default=3, help='Limit the number of examples to process (default: 3)')
    
    args = parser.parse_args()
    
    if not args.output_file:
        args.output_file = "classified_" + args.input_file
    
    process_exceptions(args.input_file, args.output_file, args.limit)
