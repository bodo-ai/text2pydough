import re

def build_metadata_lookup(metadata: list, graph_name: str):
    """
    Builds the lookup dictionary for collections and column name mappings from the updated metadata format.
    """
    graph_obj = next((g for g in metadata if g['name'] == graph_name), None)
    if not graph_obj:
        raise ValueError(f"No graph found with name {graph_name}")

    table_lookup = {}
    for collection in graph_obj["collections"]:
        table_path = collection["table path"]
        column_map = {
            prop["column name"]: prop["name"]
            for prop in collection["properties"]
            if prop["type"] == "table column"
        }
        table_lookup[table_path] = {
            "collection": collection["name"],
            "column_map": column_map
        }
    return table_lookup


def map_all_profiles_to_metadata_format(metadata: list, profiles: list, graph_name: str) -> dict:
    if not profiles:
        return {}

    table_lookup = build_metadata_lookup(metadata, graph_name)
    result = {}

    for table_profile in profiles:
        table_name = "main." + table_profile["table_name"]
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


def map_all_profiles_to_markdown(metadata: list, profiles: list, graph_name: str) -> str:
    if not profiles:
        return ""
    print(f"profiles: {profiles}")
    table_lookup = build_metadata_lookup(metadata, graph_name)
    markdown_lines = []
    markdown_lines.append(f"### The high-level graph `{graph_name}` collection contains the following columns:\n")

    for table_profile in profiles:
        table_name = "main." + table_profile["table_name"]
        if table_name not in table_lookup:
            continue

        collection_name = table_lookup[table_name]["collection"]
        markdown_lines.append(f"- **{collection_name}**: A list of {collection_name}.")
    markdown_lines.append("")

    for table_profile in profiles:
        table_name = "main." + table_profile["table_name"]
        if table_name not in table_lookup:
            continue

        collection_name = table_lookup[table_name]["collection"]
        column_map = table_lookup[table_name]["column_map"]

        markdown_lines.append(f"### The `{collection_name}` collection contains the following columns:\n")

        for original_col, profile_data in table_profile["columns"].items():
            if original_col in column_map:
                metadata_name = column_map[original_col]
                updated_profile = re.sub(
                    r'\b' + re.escape(original_col) + r'\b',
                    metadata_name,
                    profile_data["profile"]
                )
                markdown_lines.append(f"- **{metadata_name}**: {updated_profile.strip()}\n")

        markdown_lines.append("")  # Space between collections

    return "\n".join(markdown_lines)
