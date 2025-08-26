#!/usr/bin/env python3
"""
Generate a PyDough metadata graph JSON from an existing database (V2 format).

Example:
  python generate_metadata_v2.py \
      --url "sqlite:////path/to/tpch.db" \
      --graph-name TPCH \
      --output tpch_metadata_v2.json
"""
import json
import argparse
import keyword
import re
import inflect
import os
from pathlib import Path
from typing import Dict, List, Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

p = inflect.engine()

SQLITE_TYPE_MAP = {
    "INTEGER": "numeric",
    "REAL": "numeric",
    "TEXT": "string",
    "BLOB": "string",
    "NUMERIC": "numeric",
    "DATE": "datetime",
    "DATETIME": "datetime",
    "BOOLEAN": "bool"
}

CHAR_REPLACEMENTS = {
    '-': '_',
    ' ': '_',
    '²': '2',
    '³': '3',
    '¹': '1',
    '°': 'deg',
    'µ': 'u',
    '©': 'copyright',
    '®': 'registered',
    '™': 'tm',
    '€': 'eur',
    '£': 'gbp',
    '¥': 'jpy',
    '¢': 'cent',
    '¼': '1_4',
    '½': '1_2',
    '¾': '3_4',
    '+': '_plus_',
    '<': 'lt',
    '>': 'gt',
    '|': '_',
}
import builtins

# Get a list of all built-in names
BUILTINS = dir(builtins)

def make_valid_identifier(name: str) -> str:
    original_name = name

    # Add suffix for % or #
    suffix = ""
    if "%" in original_name:
        suffix = "_percentage"
    elif "#" in original_name:
        suffix = "_number"

    # Replace known special characters
    for char, replacement in CHAR_REPLACEMENTS.items():
        original_name = original_name.replace(char, replacement)

    # Replace all other non-word characters with underscores
    name = re.sub(r'\W', '_', original_name)
    name = re.sub(r'_+', '_', name).strip('_')  # Normalize underscores

    # Prepend underscore if it starts with a digit
    if name and name[0].isdigit():
        name = "_" + name

    # Append underscore if it's a Python keyword
    if keyword.iskeyword(name):
        name += "_"
    if name in BUILTINS:
        name += "_"
        
    return name + suffix

def resolve_sqlite_type(sqltype: str) -> str:
    sqltype = sqltype.upper()
    for sqlite_type, pd_type in SQLITE_TYPE_MAP.items():
        if sqlite_type in sqltype:
            return pd_type
    return "string"

def convert_column_name(col: str) -> str:
    return col.replace("#", "n_")

def get_all_columns(engine: Engine, table: str) -> List[Dict[str, Any]]:
    with engine.connect() as conn:
        table_quoted = f'"{table}"'
        result = conn.execute(text(f'PRAGMA table_info({table_quoted})'))

        columns_info = []
        for row in result:
            col_name = row[1]
            sqlite_type = row[2]
            resolved_type = resolve_sqlite_type(sqlite_type)

            sample_values = []

            #if resolved_type in ["int64", "float64"]:
                # Min and Max for numeric types
            #    stats_query = text(f'''
            #        SELECT MIN("{col_name}"), MAX("{col_name}")
            #        FROM {table_quoted}
            #        WHERE "{col_name}" IS NOT NULL
            #    ''')
            #    try:
            #        min_val, max_val = conn.execute(stats_query).fetchone()
            #        if min_val is not None and max_val is not None:
            #            sample_values = [min_val, max_val]
            #    except Exception as e:
            #        sample_values = [f"<min/max error: {e}>"]
            #else:
            #    # Up to 5 distinct samples for non-numeric
            #    sample_query = text(f'''
            #        SELECT DISTINCT "{col_name}"
            #        FROM {table_quoted}
            #        WHERE "{col_name}" IS NOT NULL
            #        LIMIT 5
            #    ''')
            #    try:
            #        sample_values = [r[0] for r in conn.execute(sample_query)]
            #    except Exception as e:
            #        print(f"Error fetching sample values for {col_name}: {e}")
            #        sample_values = [f"<sample error: {e}>"]

            columns_info.append({
                "name": col_name,
                "column name": col_name,
                "type": resolved_type,
                "description": "",
                "sample values": sample_values,
                "synonyms": []
            })
            
        return columns_info

def get_primary_keys(engine: Engine, table: str) -> List[str]:
    with engine.connect() as conn:
        from sqlalchemy.sql import text

        # Make sure table name is safely quoted
        table_quoted = f'"{table}"'  # Or use square brackets: f'[{table}]'

        result = conn.execute(text(f'PRAGMA table_info({table_quoted})'))

        primary_keys = [row[1] for row in result if row[5] > 0]
        return primary_keys

def get_foreign_keys(engine: Engine, table: str) -> List[Dict[str, Any]]:
    with engine.connect() as conn:
        table_quoted = f'"{table}"'  # Or use square brackets: f'[{table}]'
        result = conn.execute(text(f"PRAGMA foreign_key_list({table_quoted})"))
        return [
            {
                "child_table": table,
                "parent_table": row[2],
                "from_col": row[3],
                "to_col": row[4]
            }
            for row in result
        ]

def generate_metadata(engine: Engine, graph_name: str) -> Dict[str, Any]:
    insp = inspect(engine)
    tables = insp.get_table_names()

    collections = []
    collection_names = {}
    relationships = []

    for table in tables:
        cols = get_all_columns(engine, table)
        pk = get_primary_keys(engine, table)
        collection_name = make_valid_identifier(table) 
        collection_names[table] = collection_name

        if len(pk) == 1:
            unique_properties = [make_valid_identifier(pk[0])]
        elif pk:
            unique_properties = [make_valid_identifier(k) for k in pk]
        else:
            unique_properties = [[make_valid_identifier(col["name"]) for col in cols]]

        collections.append({
                "name": collection_name,
                "type": "simple table",
                "table path": f'main."{table}"' if ' ' in table or not table.isidentifier() else f"main.{table}",
                "unique properties": unique_properties,
                "properties": [
                    {
                        "name": make_valid_identifier(col["name"]),
                        "type": "table column",
                        "column name": col["column name"],
                        "data type": col["type"],
                        "description": "",
                        "sample values": [sample for sample in col["sample values"]],
                        "synonyms": []
                    }
                    
                   for col in cols
                ],
                "description": "",
                "synonyms": []
            })
    rel_pairs = set()

    for table in tables:
        fks = get_foreign_keys(engine, table)
        if fks:
            print(f"Processing foreign keys for table {table}...")
        else:
            print(f"No foreign keys found for table {table}.")
        for fk in fks:
            print(f"Found foreign key in table {table}: {fk}")
            parent = collection_names[fk["parent_table"]]
            child = collection_names[fk["child_table"]]
            parent_col = make_valid_identifier(fk["to_col"])
            child_col = make_valid_identifier(fk["from_col"])

            if (parent, child) not in rel_pairs:
                relationships.append({
                    "type": "simple join",
                    "name": parent,
                    "parent collection": child,
                    "child collection": parent,
                    "singular": True,
                    "always matches": True,
                    "keys": {child_col: [parent_col]},
                    "description": "",
                    "synonyms": []
                })
                rel_pairs.add((parent, child))

            if (child, parent) not in rel_pairs:
                relationships.append({
                    "type": "reverse",
                    "name": child,
                    "original parent": child,
                    "original property": parent,
                    "singular": False,
                    "always matches": True,
                    "description": "",
                    "synonyms": []
                })
                rel_pairs.add((child, parent))

    return [{
        "name": make_valid_identifier(graph_name),
        "version": "V2",
        "collections": collections,
        "relationships": relationships
    }]


def main():
    parser = argparse.ArgumentParser(description="Generate PyDough metadata from database")
    parser.add_argument("--url", required=True, help="Database URL (e.g., sqlite:///path/to/db.sqlite)")
    parser.add_argument("--graph-name", required=True, help="Name of the metadata graph")
    parser.add_argument("--output", required=True, help="Path to output JSON file")
    parser.add_argument("--load-graph", action="store_true", help="Also load the graph into PyDough")

    args = parser.parse_args()

    # Create engine and generate metadata
    engine = create_engine(args.url)
    metadata = generate_metadata(engine, args.graph_name)

    # Write to file
    with open(args.output, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Metadata written to {args.output}")

    # Optionally load into PyDough
    if args.load_graph:
        if not pydough:
            print("⚠️  PyDough is not installed. Skipping load.")
            return
        pydough.active_session.load_metadata_graph(args.output, args.graph_name)
        db_type = args.url.split(":")[0]
        db_path = args.url.split("///")[-1]
        pydough.active_session.connect_database(db_type, database=db_path)
        print(f"✅ Graph '{args.graph_name}' loaded and database connected.")

if __name__ == "__main__":
    main()
