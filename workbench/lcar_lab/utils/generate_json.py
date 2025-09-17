import argparse
import json
from pathlib import Path
from database_connector import Connector
from generate_knowledge_graph import generate_metadata
from sqlalchemy.engine import Engine
from sqlalchemy import inspect

# Path to the credentials file
CREDENTIALS_PATH = Path(__file__).parent / "creds.json"

def get_engine_from_credentials(config: dict) -> tuple[Engine, str]:
    """Extracts connection parameters and builds SQLAlchemy engine."""
    db_type = config.pop("engine")
    sf_schema = config.get("SF_SCHEMA", "") if db_type == "snowflake" else ""

    if db_type == "snowflake":
        conn_params = {
            "user": config["SF_USERNAME"],
            "password": config["SF_PASSWORD"],
            "account": config["SF_ACCOUNT"],
            "database": config.get("SF_DATABASE"),
            "schema": config.get("SF_SCHEMA"),
            "warehouse": config.get("SF_WH"),
            "role": config.get("SF_ROLE"),
        }
    elif db_type == "mysql":
        conn_params = {
            "username": config["username"],
            "password": config["password"],
            "host": config["host"],
            "port": config.get("port", 3306),
            "database": config["database"],
        }
    else:  # sqlite
        conn_params = {
            "database": config["db_name"]
        }

    connector = Connector(db_type, **conn_params)
    return connector.get_engine(), db_type, sf_schema

def list_all_tables_and_columns(engine: Engine, db_type: str, sf_schema: str = ""):
    """Prints all tables and columns from the database before metadata generation."""
    try:
        inspector = inspect(engine)
        tables_by_schema = {}

        if db_type == "snowflake":
            if not sf_schema:
                raise ValueError("SF_SCHEMA is required for Snowflake connections.")
            tables = inspector.get_table_names(schema=sf_schema)
            tables_by_schema[sf_schema] = tables
        else:
            default_schema = inspector.default_schema_name
            tables = inspector.get_table_names()
            tables_by_schema[default_schema] = tables

        print("Found tables in the database:")
        for schema, tbls in tables_by_schema.items():
            print(f"  • Schema '{schema}':")
            for t in tbls:
                print(f"      - {t}")
                try:
                    columns = inspector.get_columns(t, schema=schema)
                    for col in columns:
                        col_name = col["name"]
                        col_type = col["type"]
                        nullable = col.get("nullable", True)
                        print(f"          • {col_name} ({col_type}, nullable={nullable})")
                except Exception as e:
                    print(f"Failed to retrieve columns: {e}")
        print("———————————————\n")

        # Return flat list of all table names
        all_tables = [t for tbls in tables_by_schema.values() for t in tbls]
        return all_tables
    except Exception as e:
        print(f"Error: {e}")

def ask_for_table_selection(table_list: list[str]) -> list[str]:
    """Prompts the user to select tables by index or partial name."""
    print("# Tables: ")
    print(table_list, "\n")
    print("———————————————\n")
    print("\nYou can now select which tables to use for metadata generation, or empty for all tables.")
    print("Example input: 1, 4, 5 or orders, customers")
    raw_input = input("Enter comma-separated table indices or names: ").strip()
    if not raw_input:
        print("No input given, using all tables.")
        return table_list

    selections = [s.strip().lower() for s in raw_input.split(",")]

    selected_tables = []
    for idx, table_name in enumerate(table_list, 1):
        if str(idx) in selections or table_name.lower() in selections:
            selected_tables.append(table_name)

    print(f"Selected tables: {selected_tables}")
    return selected_tables

def main():
    '''
        Using this command:
        python generate_json.py --user <user> --project <project_name>
    '''
    parser = argparse.ArgumentParser(description="Generate metadata from DB using creds.json.")
    parser.add_argument("--user", required=True, help="User ID (e.g., email)")
    parser.add_argument("--project", required=True, help="Project name in creds.json")
    args = parser.parse_args()

    try:
        with open(CREDENTIALS_PATH, "r") as f:
                credentials = json.load(f)
            
        if args.user not in credentials:
            raise ValueError(f"User '{args.user}' not found in credentials file.")
        if args.project not in credentials[args.user]:
            raise ValueError(f"Project '{args.project}' not found for user '{args.user}'.")

        config = credentials[args.user][args.project]
        graph_name = config["graph_name"]
        json_output_path = Path(config["json_path"])
        
        engine, db_type, sf_schema = get_engine_from_credentials(config)
        print(f"Connecting to '{graph_name}' using engine '{db_type}'...")

        table_list = list_all_tables_and_columns(engine, db_type, sf_schema)
        selected_tables = ask_for_table_selection(table_list)

        print(f"Generating metadata for {len(selected_tables )} tables...")
        metadata = generate_metadata(engine, graph_name, db_type, selected_tables)
        print(f"Metadata generation complete.")

        json_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_output_path, "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"Metadata for '{graph_name}' written to: {json_output_path}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
