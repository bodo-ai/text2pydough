#!/usr/bin/env python3
"""
Generate a PyDough metadata graph JSON from an existing database (V2 format) and optionally load it.

Usage:
  python generate_metadata_v2.py \
      --url "sqlite:////path/to/database.sqlite" \
      --graph-name MyGraph \
      --output /path/to/output.json \
      --load-graph  # optional flag to load into PyDough session
"""

import json
import argparse
import keyword
import re
from typing import Dict, List, Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

# Optional: import pydough only if --load-graph is passed
try:
    import pydough
except ImportError:
    pydough = None

# Mapping SQLite types to simplified types
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

# Replace special characters for valid Python/SQL/JSON identifiers
CHAR_REPLACEMENTS = {
    '²': '2', '³': '3', '¹': '1', '°': 'deg', 'µ': 'u',
    '©': 'copyright', '®': 'registered', '™': 'tm',
    '€': 'eur', '£': 'gbp', '¥': 'jpy', '¢': 'cent',
    '¼': '1_4', '½': '1_2', '¾': '3_4',
    '+': '_plus_', '<': 'lt', '>': 'gt', '|': '_',
}

def make_valid_identifier(name: str) -> str:
    """Clean column/table name to be a valid identifier."""
    original_name = name.lower()

    suffix = ""
    if "%" in original_name:
        suffix = "_percentage"
    elif "#" in original_name:
        suffix = "_number"

    for char, replacement in CHAR_REPLACEMENTS.items():
        original_name = original_name.replace(char, replacement)

    name = re.sub(r'\W', '_', original_name)
    name = re.sub(r'_+', '_', name).strip('_')

    if name and name[0].isdigit():
        name = "_" + name
    if keyword.iskeyword(name):
        name += "_"

    return name + suffix

def resolve_sqlite_type(sqltype: str) -> str:
    """Map SQLite type to internal type."""
    sqltype = sqltype.upper()
    for sqlite_type, pd_type in SQLITE_TYPE_MAP.items():
        if sqlite_type in sqltype:
            return pd_type
    return "string"

def get_all_columns(engine: Engine, table: str) -> List[Dict[str, Any]]:
    """Get all columns and their metadata for a table."""
    with engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table})"))
        return [
            {
                "name": row[1],
                "column name": row[1],
                "type": resolve_sqlite_type(row[2]),
                "description": "",
                "sample values": [],
                "synonyms": []
            }
            for row in result
        ]

def get_primary_keys(engine: Engine, table: str) -> List[str]:
    """Get list of primary key columns for a table."""
    with engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table})"))
        return [row[1] for row in result if row[5] > 0]

def get_foreign_keys(engine: Engine, table: str) -> List[Dict[str, Any]]:
    """Get foreign key relationships for a table."""
    with engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA foreign_key_list({table})"))
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
    """Generate full PyDough metadata from the database."""
    insp = inspect(engine)
    tables = insp.get_table_names()

    collections = []
    collection_names = {}
    relationships = []

    for table in tables:
        cols = get_all_columns(engine, table)
        pk = get_primary_keys(engine, table)
        collection_name = table
        collection_names[table] = collection_name

        if len(pk) == 1:
            unique_properties = [make_valid_identifier(pk[0])]
        elif pk:
            unique_properties = [make_valid_identifier(k) for k in pk]
        else:
            unique_properties = [[make_valid_identifier(col["name"]) for col in cols]]

        collections.append({
            "name": make_valid_identifier(collection_name),
            "type": "simple table",
            "table path": f"main.{table}",
            "unique properties": unique_properties,
            "properties": [
                {
                    "name": make_valid_identifier(col["name"]),
                    "type": "table column",
                    "column name": col["column name"],
                    "data type": col["type"],
                    "description": "",
                    "sample values": [],
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
        for fk in fks:
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
        "name": graph_name,
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
