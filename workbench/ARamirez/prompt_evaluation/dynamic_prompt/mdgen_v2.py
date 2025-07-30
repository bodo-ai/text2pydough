import json
import sys
from pydough import parse_json_metadata_from_file
from collections import defaultdict

def generate_markdown_from_metadata(graph):
    """
    Converts a pydough graph metadata object into a formatted Markdown string..
    """
    markdown_output = []

    # Add main header and version
    markdown_output.append(f"# Metadata Overview: {graph.name} (Graph Name)")
    if hasattr(graph, 'version') and graph.version:
        markdown_output.append(f"**Version**: {graph.version}")
    markdown_output.append("")

    # Iterate through each collection (table) in the graph
    for collection_name in graph.get_collection_names():
        collection = graph.get_collection(collection_name)
        markdown_output.append(f"### The `{collection.name}` collection contains the following columns:")

        # Iterate through each property (column or relationship) within the collection
        for prop_name in collection.get_property_names():
            prop = collection.get_property(prop_name)
            if not prop:
                continue

            # Handle scalar properties (regular columns)
            if not prop.is_subcollection:
                description_text = prop.description if prop.description else "No description available."
                markdown_output.append(f"- **{prop.name}**: {description_text}")

                if hasattr(prop, 'synonyms') and prop.synonyms:
                    markdown_output.append(f"  - Synonyms: {', '.join(prop.synonyms)}")
                if hasattr(prop, 'sample_values') and prop.sample_values:
                    sample_values_str = ', '.join(map(str, prop.sample_values))
                    markdown_output.append(f"  - Sample values: {sample_values_str}")
            # Handle sub-collection properties (relationships)
            else:
                description_text = prop.description if prop.description else "No description available."
                reverse_info_suffix = ""

                # Determine the "reverse of" text for relationships
                if hasattr(graph, 'relationships'):
                    for rel_entry in graph.relationships:
                        # If the current property is a 'reverse' relationship itself
                        if rel_entry.get("type") == "reverse" and rel_entry.get("name") == prop.name:
                            is_relevant_reverse = False
                            for sj_rel in graph.relationships:
                                if sj_rel.get("type") == "simple join" and \
                                   sj_rel.get("parent collection") == rel_entry.get("original parent") and \
                                   sj_rel.get("name") == rel_entry.get("original property") and \
                                   sj_rel.get("child collection") == collection.name:
                                    is_relevant_reverse = True
                                    break
                            if is_relevant_reverse:
                                reverse_info_suffix = f" (reverse of `{rel_entry['original parent']}.{rel_entry['original property']}`)"
                                break
                        # If the current property is a 'simple join' relationship
                        elif rel_entry.get("type") == "simple join" and rel_entry.get("name") == prop.name and \
                             rel_entry.get("parent collection") == collection.name and \
                             rel_entry.get("child collection") == prop.child_collection.name:
                            
                            # Find the corresponding reverse relationship
                            for rev_rel_entry in graph.relationships:
                                if rev_rel_entry.get("type") == "reverse" and \
                                   rev_rel_entry.get("original parent") == rel_entry.get("child collection") and \
                                   rev_rel_entry.get("original property") == rel_entry.get("name"):
                                    reverse_info_suffix = f" (reverse of `{rel_entry['child collection']}.{rev_rel_entry['name']}`)"
                                    break
                            if reverse_info_suffix:
                                break

                markdown_output.append(f"- **{prop.name}**: {description_text}{reverse_info_suffix}")

                if hasattr(prop, 'synonyms') and prop.synonyms:
                    if isinstance(prop.synonyms, str):
                        markdown_output.append(f"  - Synonyms: {prop.synonyms}")
                    else:
                        markdown_output.append(f"  - Synonyms: {', '.join(prop.synonyms)}")
        markdown_output.append("") # Add a blank line between collections

    return "\n".join(markdown_output)

# Command-line interface (CLI) usage
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python your_script_name.py <input_json_file_path>")
        sys.exit(1)

    input_file_path = sys.argv[1]

    try:
        # Load JSON to extract graph name for pydough parsing
        with open(input_file_path, 'r', encoding='utf-8') as f:
            metadata_json = json.load(f)

        graph_name = metadata_json[0].get('name', 'default_graph')

        # Parse the metadata file using pydough
        my_graph = parse_json_metadata_from_file(input_file_path, graph_name)

        # Generate the markdown content
        markdown_content = generate_markdown_from_metadata(my_graph)

        # Define output file name
        output_file_name = f"{graph_name}_graph.md"

        # Save the markdown content to a file
        with open(output_file_name, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"Markdown successfully generated and saved to '{output_file_name}'")

    except FileNotFoundError:
        print(f"Error: The file '{input_file_path}' was not found. Please check the path.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{input_file_path}'. Please ensure it's a valid JSON file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        

def json_to_markdown(metadata: list) -> str:
    markdown = []

    for graph in metadata:
        graph_name = graph["name"]
        collections = {col["name"]: col for col in graph["collections"]}
        relationships = graph.get("relationships", [])
        fields_per_collection = {}
        
        # Create relationship mappings
        forward_relationships = defaultdict(list)
        reverse_relationships = defaultdict(list)
        relationship_by_name = {}

        # Process relationships
        for rel in relationships:
            relationship_by_name[rel["name"]] = rel
            
            if rel["type"] == "simple join":
                # Forward relationship: parent -> child
                forward_relationships[rel["parent collection"]].append(rel)
            elif rel["type"] == "reverse":
                # Reverse relationship: child -> parent
                # Find the original relationship and map it to the child collection
                original_prop = rel["original property"]
                original_parent = rel["original parent"]
                # The reverse relationship should be added to the child collection
                # of the original relationship
                if original_prop in relationship_by_name:
                    original_rel = relationship_by_name[original_prop]
                    child_collection = original_rel["child collection"]
                    print(f"Adding reverse relationship {rel['name']} to {child_collection} and original rel {original_rel['name']}")
                    reverse_relationships[child_collection].append(rel)

        # Header: list of collections
        markdown.append(f"### The high-level graph `{graph_name}` collection contains the following collections:")
        for collection_name in collections:
            markdown.append(f"- **{collection_name}**: A list of {collection_name}.")
        markdown.append("")

        # Collection-level details
        for collection_name, collection in collections.items():
            markdown.append(f"### The `{collection_name}` collection contains the following columns:")
            props = collection.get("properties", [])
            prop_map = {p["name"]: p for p in props}
            fields_per_collection[collection_name] = list(prop_map.keys())

            # Table columns
            for prop_name, prop_info in prop_map.items():
                if prop_info["type"] == "table column":
                    desc_lines = [f"- **{prop_name}**"]

                    # Description
                    description = prop_info.get("description")
                    if description:
                        desc_lines[0] += f": {description}"
                    else:
                        desc_lines[0] += f": {get_column_description(prop_name)}"

                    # Sample values
                    sample_values = prop_info.get("sample values", [])
                    if sample_values:
                        values = ", ".join(str(v) for v in sample_values)
                        desc_lines.append(f"  - Example values: `{values}`")

                    # Synonyms
                    synonyms = prop_info.get("synonyms", [])
                    if synonyms:
                        synonyms_str = ", ".join(synonyms)
                        desc_lines.append(f"  - Synonyms: _{synonyms_str}_")

                    markdown.extend(desc_lines)

            # Forward (simple join) relationships
            for rel in forward_relationships.get(collection_name, []):
                name = rel["name"]
                other = rel["child collection"]
                plural = not rel.get("singular", True)
                desc_lines = [f"- **{name}**"]

                # Description
                description = rel.get("description")
                if description:
                    desc_lines[0] += f": {description}"
                else:
                    desc_lines[0] += f": A list of all {other} associated with this record." if plural \
                        else f": The corresponding {other} for this record."

                markdown.extend(desc_lines)
                if rel.get("synonyms"):
                    markdown.append(f"  - Synonyms: _{', '.join(rel['synonyms'])}_")

            # Reverse relationships
            for rel in reverse_relationships.get(collection_name, []):
                name = rel["name"]
                original_parent = rel["original parent"]
                plural = not rel.get("singular", True)
                desc_lines = [f"- **{name}**"]
                
                description = rel.get("description")
                if description:
                    desc_lines[0] += f": {description}"
                else:
                    desc_lines[0] += f": A list of all {original_parent} associated with this record." if plural \
                        else f": The corresponding {original_parent} for this record."
                
                markdown.extend(desc_lines)
                if rel.get("synonyms"):
                    markdown.append(f"  - Synonyms: _{', '.join(rel['synonyms'])}_")

            markdown.append("")

        # Auto-generated query examples
        markdown.append("### Example Relationship Queries (Auto-generated)")
        markdown.append("")

        for collection_name in collections:

            # Forward relationship examples
            for rel in forward_relationships.get(collection_name, []):
                other = rel["child collection"]
                plural = not rel.get("singular", True)
                fields = fields_per_collection.get(other, [])[:6]
                fields_str = ", ".join(fields) if fields else "..."
                markdown.append(
                    f"To get {'all' if plural else 'the corresponding'} `{other}` from each `{collection_name}`:")
                markdown.append(f"```python\n{collection_name}.{rel['name']}.CALCULATE({fields_str})\n```")
                print(f"Adding forward relationship example for {collection_name}.{rel['name']} with fields {fields_str}")

                markdown.append("")

            # Reverse relationship examples
            for rel in reverse_relationships.get(collection_name, []):
                original_parent = rel["original parent"]
                reverse_name = rel["name"]
                plural = not rel.get("singular", True)
                reverse_fields = fields_per_collection.get(original_parent, [])[:6]
                reverse_str = ", ".join(reverse_fields) if reverse_fields else "..."
                markdown.append(
                    f"To get {'all' if plural else 'the corresponding'} `{original_parent}` from each `{collection_name}`:")
                markdown.append(f"```python\n{collection_name}.{reverse_name}.CALCULATE({reverse_str})\n```")
                print(f"Adding reverse relationship example for {collection_name}.{reverse_name} with fields {reverse_str}")
                markdown.append("")

    return "\n".join(markdown)


def get_column_description(name):
    name_map = {
        "key": "A unique identifier",
        "name": "The name",
        "comment": "Additional comments or notes",
        "address": "The address",
        "phone": "The phone number",
        "email": "The email",
    }
    if name in name_map:
        return name_map[name]
    elif name.endswith("_key"):
        ref = name.replace("_key", "")
        return f"A foreign key referencing the `{ref}s` collection."
    else:
        return f"{name.replace('_', ' ').capitalize()}."


