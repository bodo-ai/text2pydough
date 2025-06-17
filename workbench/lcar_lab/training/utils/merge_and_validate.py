import json
import argparse
import os
from datetime import datetime
from pathlib import Path


def is_valid_entry(entry):
    try:
        if 'systemInstruction' not in entry or 'contents' not in entry:
            return False

        sys = entry['systemInstruction']
        if sys.get('role') != 'system':
            return False
        if not isinstance(sys.get('parts'), list) or not sys['parts']:
            return False
        if 'text' not in sys['parts'][0]:
            return False

        contents = entry['contents']
        if not isinstance(contents, list) or not contents:
            return False
        for part in contents:
            if part.get('role') not in ('user', 'model', 'assistant'):
                return False
            parts = part.get('parts')
            if not isinstance(parts, list) or not parts:
                return False
            data = parts[0]
            if not ('text' in data or 'fileData' in data):
                return False
        return True
    except Exception as e:
        print(f"Validation error: {e}")
        return False


def load_and_validate_jsonl(file_path):
    valid_entries = []
    with open(file_path, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line)
                if is_valid_entry(entry):
                    valid_entries.append(entry)
            except json.JSONDecodeError:
                print(f"Skipping malformed line in {file_path}")
    print(f"{file_path}: {len(valid_entries)} valid entries")
    return valid_entries


def process_directory(directory):
    # First try 'val_sample_training_data.jsonl' and then fallback to 'train.jsonl' for validation data
    valid_file = os.path.join(directory, 'val_sample_training_data.jsonl') if os.path.exists(os.path.join(directory, 'val_sample_training_data.jsonl')) else os.path.join(directory, 'train.jsonl')
    
    # First try 'train_sample_training_data.jsonl' and then fallback to 'validation.jsonl' for training data
    train_file = os.path.join(directory, 'train_sample_training_data.jsonl') if os.path.exists(os.path.join(directory, 'train_sample_training_data.jsonl')) else os.path.join(directory, 'validation.jsonl')

    all_valid_entries = []
    all_train_entries = []

    # Check and process valid_file
    if os.path.exists(valid_file):
        print(f"Processing {valid_file}...")
        all_valid_entries.extend(load_and_validate_jsonl(valid_file))
    else:
        print(f"Warning: {valid_file} not found. Skipping.")

    # Check and process train_file
    if os.path.exists(train_file):
        print(f"Processing {train_file}...")
        all_train_entries.extend(load_and_validate_jsonl(train_file))
    else:
        print(f"Warning: {train_file} not found. Skipping.")

    return all_valid_entries, all_train_entries


def main():
    parser = argparse.ArgumentParser(description="Merge and validate JSONL training datasets from directories")
    parser.add_argument('dirs', nargs='+', help="Paths to directories containing valid.jsonl and train.jsonl files")
    parser.add_argument('--output_dir', default="/home/ara/mount-folder/datasets/Finetuning/training_data/labeled_data/spider_kaggledbqa/training_ready/20250502_121235", help="Output directory")
    parser.add_argument('--output_name_valid', default="val_sample_training_data.jsonl", help="Custom name for the output valid file (e.g., merged_valid.jsonl)")
    parser.add_argument('--output_name_train', default="train_sample_training_data.jsonl", help="Custom name for the output train file (e.g., merged_train.jsonl)")

    args = parser.parse_args()

    all_valid_entries = []
    all_train_entries = []
    for directory in args.dirs:
        print(f"Processing directory: {directory}")
        valid_entries, train_entries = process_directory(directory)
        all_valid_entries.extend(valid_entries)
        all_train_entries.extend(train_entries)

    # Ensure the output directory exists
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    subdir = Path(args.output_dir) / timestamp
    subdir.mkdir(parents=True, exist_ok=True)

    # Output paths
    output_valid_path = subdir / args.output_name_valid
    output_train_path = subdir / args.output_name_train

    # Save merged valid entries to valid.jsonl
    with open(output_valid_path, 'w') as f:
        for entry in all_valid_entries:
            f.write(json.dumps(entry) + '\n')

    print(f"Merged and validated valid entries saved to {output_valid_path}")

    # Save merged train entries to train.jsonl
    with open(output_train_path, 'w') as f:
        for entry in all_train_entries:
            f.write(json.dumps(entry) + '\n')

    print(f"Merged and validated train entries saved to {output_train_path}")

    # Final validation of saved files
    print(f"\nValidating output files...")

    # Validate valid.jsonl
    final_valid_entries = []
    with open(output_valid_path, 'r') as f:
        for i, line in enumerate(f, 1):
            try:
                obj = json.loads(line)
                if not is_valid_entry(obj):
                    print(f"⚠️  Invalid format at line {i} in valid.jsonl")
                else:
                    final_valid_entries.append(obj)
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error at line {i}: {e}")

    print(f"\n✅ Final validation complete for valid.jsonl: {len(final_valid_entries)} valid entries.")

    # Validate train.jsonl
    final_train_entries = []
    with open(output_train_path, 'r') as f:
        for i, line in enumerate(f, 1):
            try:
                obj = json.loads(line)
                if not is_valid_entry(obj):
                    print(f"⚠️  Invalid format at line {i} in train.jsonl")
                else:
                    final_train_entries.append(obj)
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error at line {i}: {e}")

    print(f"\n✅ Final validation complete for train.jsonl: {len(final_train_entries)} valid entries.\n")


if __name__ == "__main__":
    main()
