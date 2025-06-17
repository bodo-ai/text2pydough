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

def resolve_sqlite_type(sqltype: str) -> str:
    sqltype = sqltype.upper()
    for sqlite_type, pd_type in SQLITE_TYPE_MAP.items():
        if sqlite_type in sqltype:
            return pd_type
    return "string"

def convert_column_name(col: str) -> str:
    return col.lower().replace("#", "n_")

def get_all_columns(engine: Engine, table: str) -> List[Dict[str, Any]]:
    with engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table})"))
        return [
            {
                "name": row[1].lower(),
                "column name": row[1],
                "type": resolve_sqlite_type(row[2]),
                "description": "",
                "sample values": [],
                "synonyms": []
            }
            for row in result
        ]

def get_primary_keys(engine: Engine, table: str) -> List[str]:
    with engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table})"))
        return [row[1].lower() for row in result if row[5] > 0]

def get_foreign_keys(engine: Engine, table: str) -> List[Dict[str, Any]]:
    with engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA foreign_key_list({table})"))
        return [
            {
                "child_table": table,
                "parent_table": row[2],
                "from_col": row[3].lower(),
                "to_col": row[4].lower()
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
        collection_name = p.plural(table.lower()) if not table.lower().endswith("s") else table.lower()
        collection_names[table] = collection_name

        collections.append({
            "name": collection_name,
            "type": "simple table",
            "table path": f"main.{table.upper()}",
            "unique properties": pk if len(pk) == 1 else [pk],
            "properties": [
                {
                    "name": col["name"],
                    "type": "table column",
                    "column name": col["column name"].upper(),
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
            parent_col = fk["to_col"]
            child_col = fk["from_col"]

            if (parent, child) not in rel_pairs:
                relationships.append({
                    "type": "simple join",
                    "name": parent,
                    "parent collection": parent,
                    "child collection": child,
                    "singular": True,
                    "always matches": True,
                    "keys": {parent_col: [child_col]},
                    "description": "",
                    "synonyms": []
                })
                rel_pairs.add((parent, child))

            if (child, parent) not in rel_pairs:
                relationships.append({
                    "type": "reverse",
                    "name": child,
                    "original parent": parent,
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="SQLAlchemy SQLite URL")
    parser.add_argument("--graph-name", required=True, help="Graph name")
    parser.add_argument("--output", required=True, help="Output path for metadata JSON")
    args = parser.parse_args()

    engine = create_engine(args.url)
    metadata = generate_metadata(engine, args.graph_name)

    with open(args.output, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Metadata written to {args.output}")

if __name__ == "__main__":
    main()
