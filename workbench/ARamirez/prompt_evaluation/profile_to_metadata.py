import re

def map_all_profiles_to_metadata_format(metadata: dict, profiles: list, graph_name) -> dict:
    """
    Maps all table profiles to metadata property names, updates profile descriptions,
    and returns a dictionary where each key is the table name and value is:
    {
      "collection": "CollectionName",
      "columns": {
        "property_name": {
          "profile": "Updated profile description"
        }
      }
    }

    Args:
        metadata (dict): The metadata JSON.
        profiles (list): The profile JSON list.

    Returns:
        dict: Mapping from table name to collection info and cleaned-up profiles.
    """
    if not profiles:
        return {}

    result = {}

    # Build lookup: {table_path: (collection_name, {column_name: property_name})}
    table_lookup = {}
    for collection_name, collection in metadata[graph_name].items():
        table_path = collection["table_path"]
        column_map = {
            prop_info["column_name"]: prop_name
            for prop_name, prop_info in collection["properties"].items()
            if prop_info["type"] == "table_column"
        }
        table_lookup[table_path] = {
            "collection": collection_name,
            "column_map": column_map
        }

    # Process each profile entry
    for table_profile in profiles:
        table_name = "".join(["main.",table_profile["table_name"]])
        if table_name not in table_lookup:
            continue

        collection_name = table_lookup[table_name]["collection"]
        column_map = table_lookup[table_name]["column_map"]

        columns_output = {}
        for original_col, profile_data in table_profile["columns"].items():
            if original_col in column_map:
                metadata_name = column_map[original_col]
                updated_profile = re.sub(
                    r'\b' + re.escape(original_col) + r'\b',
                    metadata_name,
                    profile_data["profile"]
                )
                columns_output[metadata_name] = {
                    "profile": updated_profile
                }

        if columns_output:
            result[table_name] = {
                "collection": collection_name,
                "columns": columns_output
            }
    return result

def map_all_profiles_to_markdown(metadata: dict, profiles: list, graph_name: str) -> str:
    """
    Converts table and column profile metadata into a structured Markdown document,
    including joins.

    Args:
        metadata (dict): The metadata JSON with table and column mappings.
        profiles (list): The list of profile information per table.
        graph_name (str): The graph name used to access metadata.

    Returns:
        str: A formatted Markdown string documenting the schema.
    """
    if not profiles:
        return ""

    markdown_lines = []

    # Build lookup: {table_path: (collection_name, {column_name: property_name})}
    table_lookup = {}
    for collection_name, collection in metadata[graph_name].items():
        table_path = collection["table_path"]
        column_map = {
            prop_info["column_name"]: prop_name
            for prop_name, prop_info in collection["properties"].items()
            if prop_info["type"] == "table_column"
        }
        table_lookup[table_path] = {
            "collection": collection_name,
            "column_map": column_map
        }

    markdown_lines.append(f"### The high-level graph `{graph_name}` collection contains the following columns:\n")
    for table_profile in profiles:
        table_name = "main." + table_profile["table_name"]
        if table_name not in table_lookup:
            continue

        collection_name = table_lookup[table_name]["collection"]
        markdown_lines.append(f"- **{collection_name}**: A list of {collection_name}.")
    markdown_lines.append("")  # Add spacing

    # Process each table profile
    for table_profile in profiles:
        table_name = "main." + table_profile["table_name"]
        if table_name not in table_lookup:
            continue

        collection_name = table_lookup[table_name]["collection"]
        column_map = table_lookup[table_name]["column_map"]

        markdown_lines.append(f"### The `{collection_name}` collection contains the following columns:\n")

        # Add table_column profiles
        for original_col, profile_data in table_profile["columns"].items():
            if original_col in column_map:
                metadata_name = column_map[original_col]
                updated_profile = re.sub(
                    r'\b' + re.escape(original_col) + r'\b',
                    metadata_name,
                    profile_data["profile"]
                )
                markdown_lines.append(f"- **{metadata_name}**: {updated_profile.strip()}\n")

        # Add simple_join fields
        for prop_name, prop_info in metadata[graph_name][collection_name]["properties"].items():
            if prop_info["type"] == "simple_join":
                join_type = "singular" if prop_info.get("singular", False) else "plural/list"
                join_target = prop_info["other_collection_name"]
                join_keys = prop_info["keys"]
                join_desc = f"{join_type} collection of `{join_target}`"
                markdown_lines.append(f"- **{prop_name}**: {join_desc}\n")

        markdown_lines.append("")  # Space between collections
    print(f"Markdwon: {markdown_lines}")
    return "\n".join(markdown_lines)