import pandas as pd
import json
from pathlib import Path
from sklearn.model_selection import train_test_split
import os

# Configuration
SYSTEM_INSTRUCTION = "You are an analytics expert and a proficient Pydough generator that creates Python code based on natural language descriptions."

def convert_to_json_format(row):
    """Convert a row to the required JSON format."""
    return {
        "systemInstruction": {
            "role": "system",
            "parts": [
                {
                    "text": SYSTEM_INSTRUCTION
                }
            ]
        },
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": row['question']
                    }
                ]
            },
            {
                "role": "model",
                "parts": [
                    {
                        "text": row['generated_answer']
                    }
                ]
            }
        ]
    }

def save_jsonl(data, filepath):
    """Save data to a JSONL file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')

def main():
    # Input and output paths
    input_csv = Path(__file__).parent / 'training_data' / 'labeled_data' / 'basicQ' / 'processed' / '20250502_144410' / 'generated_answers.csv'
    output_dir = Path(__file__).parent / 'training_data' / 'labeled_data' / 'basicQ' / 'training_ready'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load the CSV file
    df = pd.read_csv(input_csv)
    
    # Split into train and validation sets
    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)
    
    # Convert to JSON format
    train_data = [convert_to_json_format(row) for _, row in train_df.iterrows()]
    val_data = [convert_to_json_format(row) for _, row in val_df.iterrows()]
    
    # Save to JSONL files
    save_jsonl(train_data, output_dir / 'train.jsonl')
    save_jsonl(val_data, output_dir / 'validation.jsonl')
    
    print(f"Successfully converted data to JSONL format:")
    print(f"Training samples: {len(train_data)}")
    print(f"Validation samples: {len(val_data)}")
    print(f"Files saved to: {output_dir}")

if __name__ == "__main__":
    main() 