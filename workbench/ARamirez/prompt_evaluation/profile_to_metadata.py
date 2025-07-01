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
    result = {}

    if profiles is None:
        return result
    
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
        table_name = table_profile["table_name"]
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
