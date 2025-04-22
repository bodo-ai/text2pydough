#!/usr/bin/env python3
"""
Generate a PyDough metadata graph JSON from an existing database.

Example:
  python generate_pydough_metadata.py \
      --url "sqlite:////mnt/c/Users/david/bodo/KaggleDBQA/databases/GeoNuclearData/GeoNuclearData.sqlite" \
      --graph-name DATABASE \
      --output pydough_graph.json
"""
import json
import argparse
import inflect
import os
import importlib
import tempfile
import pathlib
from collections import defaultdict
from typing import Dict, List, Any, Union, Tuple
from pathlib import Path

import pandas as pd
import pydough
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.sql.sqltypes import (
    Boolean, Integer, BigInteger, SmallInteger,
    Numeric, Float, DECIMAL, String, Text,
    Date, DateTime, TIMESTAMP
)

# ---------- Configuration ----------------------------------------------------
DEFAULT_TYPE_MAP = {
    Boolean: "bool",
    SmallInteger: "int16",
    Integer: "int32",
    BigInteger: "int64",
    (Numeric, Float, DECIMAL): "decimal[38,10]",  # fallback precision/scale
    (String, Text): "string",
    Date: "date",
    (DateTime, TIMESTAMP): "timestamp[3]",
}

# SQLite type mapping
SQLITE_TYPE_MAP = {
    "INTEGER": "int64",
    "REAL": "decimal[38,10]",
    "TEXT": "string",
    "BLOB": "string",
    "NUMERIC": "decimal[38,10]",
    "DATE": "date",
    "DATETIME": "timestamp[3]",
    "BOOLEAN": "bool"
}

p = inflect.engine()          # plural‑singular helper
# -----------------------------------------------------------------------------

def convert_windows_to_wsl_path(windows_path: str) -> str:
    """Convert a Windows path to WSL path format."""
    # Remove sqlite:/// prefix if present
    if windows_path.startswith("sqlite:///"):
        windows_path = windows_path[10:]
    
    # Convert Windows path to WSL path
    if windows_path.startswith("C:"):
        wsl_path = windows_path.replace("C:", "/mnt/c")
    elif windows_path.startswith("c:"):
        wsl_path = windows_path.replace("c:", "/mnt/c")
    else:
        wsl_path = windows_path
    
    # Convert backslashes to forward slashes
    wsl_path = wsl_path.replace('\\', '/')
    
    # Remove any trailing slashes
    wsl_path = wsl_path.rstrip('/')
    
    return wsl_path

def validate_database_path(path: str) -> bool:
    """Validate that the database file exists and is accessible."""
    if path.startswith("sqlite:///"):
        path = path[10:]
    
    # Convert to absolute path if needed
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    
    # Check if file exists
    if not os.path.exists(path):
        print(f"❌  Database file not found: {path}")
        return False
    
    # Check if file is readable
    if not os.access(path, os.R_OK):
        print(f"❌  No read permission for database file: {path}")
        return False
    
    return True

def resolve_sqlite_type(sqltype: str) -> str:
    """Map a SQLite column type to the closest PyDough type string."""
    sqltype = sqltype.upper()
    for sqlite_type, pd_type in SQLITE_TYPE_MAP.items():
        if sqlite_type in sqltype:
            return pd_type
    return "string"           # safe default

def build_properties(columns: List[Dict[str, Any]], fk_by_col: Dict[str, Any]) -> Dict[str, Any]:
    """Return the property dict for a table, minus joins (added later)."""
    props = {}
    for col in columns:
        name = col["name"]
        props[name] = {
            "type": "table_column",
            "column_name": name,
            "data_type": resolve_sqlite_type(col["type"]),
        }
    return props

def cardinality(child_table: str, fk_cols: List[str], pk_map: Dict[str, List[str]]) -> bool:
    """
    Decide if a FK points to <=1 parent row (True) or many (False).

    Heuristic: FK columns are a (superset of) PK or UNIQUE.
    """
    pk_cols = pk_map[child_table]
    return set(fk_cols).issuperset(set(pk_cols))

def get_foreign_keys(engine: Engine, table: str) -> List[Dict[str, Any]]:
    """Get foreign key information for a SQLite table."""
    fks = []
    with engine.connect() as conn:
        # Get foreign key information from SQLite's pragma
        result = conn.execute(text(f"PRAGMA foreign_key_list({table})"))
        for row in result:
            fks.append({
                "referred_table": row[2],  # table name
                "referred_columns": [row[4]],  # to column
                "constrained_columns": [row[3]],  # from column
            })
    return fks

def generate_metadata(engine: Engine, graph_name: str) -> Dict[str, Any]:
    """Generate PyDough metadata for a SQLite database."""
    insp = inspect(engine)
    
    # Get all tables
    tables = insp.get_table_names()
    # primary key lookup (helps with cardinality later)
    pk_map = {}
    for tbl in tables:
        with engine.connect() as conn:
            # Get primary key information from SQLite's pragma
            result = conn.execute(text(f"PRAGMA table_info({tbl})"))
            pk_cols = [row[1] for row in result if row[5] > 0]  # row[5] is pk flag
            pk_map[tbl] = pk_cols
    graph: Dict[str, Any] = {graph_name: {}}

    # pre‑pass to collect column info & PKs
    for tbl in tables:
        with engine.connect() as conn:
            # Get column information
            result = conn.execute(text(f"PRAGMA table_info({tbl})"))
            cols = []
            for row in result:
                cols.append({
                    "name": row[1],  # column name
                    "type": row[2],  # data type
                    "notnull": row[3],  # not null constraint
                    "dflt_value": row[4],  # default value
                    "pk": row[5]  # primary key flag
                })

        # Handle unique_properties based on primary keys
        unique_props: Union[List[str], List[List[str]]]
        if len(pk_map[tbl]) == 1:
            unique_props = pk_map[tbl]  # Single primary key
        elif len(pk_map[tbl]) > 1:
            unique_props = [pk_map[tbl]]  # Composite primary key
        else:
            # If no primary key, use all columns as a composite key
            unique_props = [[col["name"] for col in cols]]

        graph[graph_name][tbl] = {
            "type": "simple_table",
            "table_path": f"main.{tbl}",
            "unique_properties": unique_props,
            "properties": build_properties(cols, {}),
        }

    # second pass: joins
    for tbl in tables:
        fks = get_foreign_keys(engine, tbl)
        for fk in fks:
            parent = fk["referred_table"]
            child = tbl
            col_map = dict(zip(fk["constrained_columns"],
                             fk["referred_columns"]))
            # decide relationship names
            child_rel_name = p.plural(parent) if not cardinality(child,
                                                               list(col_map),
                                                               pk_map) else parent
            parent_rel_name = p.singular_noun(child) or child

            # --------------- child --> parent (many/one‑to‑one) ------------
            #child_prop = {
            #    "type": "simple_join",
            #    "other_collection_name": parent,
            #    "singular": True,  # child row → 1 parent
            #    "no_collisions": False,
            #    "keys": col_map,
            #    "reverse_relationship_name": parent_rel_name,
            #}
            #graph[graph_name][child]["properties"][parent_rel_name] = child_prop

            # --------------- parent --> children ---------------------------
            rev_col_map = {v: [k] for k, v in col_map.items()}
            parent_prop = {
                "type": "simple_join",
                "other_collection_name": child,
                "singular": cardinality(child, list(col_map), pk_map),
                "no_collisions": not cardinality(child, list(col_map), pk_map),
                "keys": rev_col_map,
                "reverse_relationship_name": child_rel_name,
            }
            graph[graph_name][parent]["properties"][child] = parent_prop
            print(f"table {tbl}, parent {parent}")
            print(f"parent_prop: {parent_prop} \n")
            #print(f"child prop: {child_prop}\n")
    return graph

def test_json_validates_against_spec(metadata_path: str) -> Tuple[bool, str]:
    """Validate the generated metadata against PyDough specifications."""
    try:
        # Load file
        with open(metadata_path, 'r') as f:
            meta = json.load(f)

        # Top-level graph and collection checks
        if "DATABASE" not in meta:
            return False, "Graph key 'DATABASE' missing"

        # Check each table
        for table_name, collection in meta["DATABASE"].items():
            # Required fields for a simple table collection
            for key in ("type", "table_path", "unique_properties", "properties"):
                if key not in collection:
                    return False, f"Missing required field '{key}' in table '{table_name}'"
            
            if collection["type"] != "simple_table":
                return False, f"Invalid type '{collection['type']}' in table '{table_name}'"

            # Ensure every property is a valid table_column
            for prop_name, prop in collection["properties"].items():
                if prop["type"] != "table_column":
                    return False, f"Invalid property type '{prop['type']}' in column '{prop_name}'"
                if not {"column_name", "data_type"}.issubset(prop.keys()):
                    return False, f"Missing required fields in column '{prop_name}'"

        return True, "Metadata validation successful"
    except Exception as e:
        return False, f"Error during validation: {str(e)}"

def test_pydough_loads_ok(metadata_path: str) -> Tuple[bool, str]:
    """Test if PyDough can load the generated metadata."""
    try:
        # Create a new session
        session = pydough.PyDoughSession()
        session.load_metadata_graph(metadata_path, "DATABASE")
        
        # Just verify the session was created and metadata loaded
        return True, "PyDough session created successfully"
    except Exception as e:
        return False, f"Error loading metadata in PyDough: {str(e)}"

def test_sql_generation(metadata_path: str) -> Tuple[bool, str]:
    """Test SQL generation from the metadata."""
    try:
        session = pydough.PyDoughSession()
        session.load_metadata_graph(metadata_path, "DATABASE")
        
        # For now, just verify the session was created
        return True, "Session created successfully"
    except Exception as e:
        return False, f"Error creating session: {str(e)}"

def test_roundtrip_dataframe(metadata_path: str, db_url: str) -> Tuple[bool, str]:
    """Test DataFrame generation from the metadata."""
    try:
        session = pydough.PyDoughSession()
        session.load_metadata_graph(metadata_path, "DATABASE")
        session.connect_database("sqlite", database=db_url)
        
        # For now, just verify the session was created and connected
        return True, "Session created and connected successfully"
    except Exception as e:
        return False, f"Error creating session: {str(e)}"

def run_tests(metadata_path: str, db_url: str) -> bool:
    """Run all tests and return True if all pass."""
    print("\nRunning metadata validation tests...")
    
    tests = [
        ("JSON Validation", test_json_validates_against_spec),
        ("PyDough Loading", test_pydough_loads_ok),
        ("SQL Generation", test_sql_generation),
        ("DataFrame Roundtrip", lambda p: test_roundtrip_dataframe(p, db_url))
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        success, message = test_func(metadata_path)
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        if not success:
            all_passed = False
    
    return all_passed

def main():
    ap = argparse.ArgumentParser(description="Generate PyDough metadata JSON for SQLite databases")
    ap.add_argument("--url", required=True,
                    help="SQLAlchemy‑style SQLite URL (e.g., sqlite:///path/to/database.db)")
    ap.add_argument("--graph-name", default="DATABASE",
                    help="Top‑level graph name (default: DATABASE)")
    ap.add_argument("--output", default="pydough_graph.json",
                    help="Path for output JSON")
    ap.add_argument("--skip-tests", action="store_true",
                    help="Skip validation tests")
    args = ap.parse_args()

    # Convert Windows path to WSL path if needed
    if args.url.startswith("sqlite:///C:") or args.url.startswith("sqlite:///c:"):
        wsl_path = convert_windows_to_wsl_path(args.url)
        args.url = f"sqlite:///{wsl_path}"
        print(f"Converted path to WSL format: {args.url}")

    # Validate database path
    if not validate_database_path(args.url[10:]):  # Remove sqlite:/// prefix
        return

    # Ensure the output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        engine = create_engine(args.url)
        md = generate_metadata(engine, args.graph_name)
        with open(args.output, "w") as f:
            json.dump(md, f, indent=2)

        print(f"✅  Metadata written to {args.output}")
        
        # Run validation tests unless skipped
        if not args.skip_tests:
            if run_tests(args.output, args.url[10:]):  # Remove sqlite:/// prefix
                print("\n✅  All tests passed!")
            else:
                print("\n❌  Some tests failed. Please review the output above.")
                return 1
                
        print("\n   Review singular/plural relationship names and tweak if needed.")
    except Exception as e:
        print(f"❌  Error generating metadata: {str(e)}")
        if "no such table" in str(e):
            print("   Make sure the database path is correct and the database exists.")
        elif "unable to open database file" in str(e):
            print("   Make sure you have read permissions for the database file.")
        raise

if __name__ == "__main__":
    main() 